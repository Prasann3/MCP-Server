import socket
import asyncio
import json
import signal
import psutil
import math
import time
from app.services.redis import redis_client
from app.core.logging import logging
from app.utils.utility import get_postman_port, register_to_postman

logger = logging.getLogger("monitorer")

class Monitorer:
    def __init__(self, check_interval=5):
        self.interval = check_interval
        self.is_running = True
        
        # Internal State
        self.redis_client = redis_client
        self.current_worker_counts = {"parser": 1, "uploader": 1}
        
        # Constants
        self.PARSING_THRESHOLD = 8   
        self.UPLOAD_THRESHOLD = 12   
        self.CPU_CRITICAL = 90.0     
        self.RAM_SAFE_BUFFER = 0.89
        
        # Idle Logic
        self.IDLE_DOWN_TIME = 45 # Seconds of zero queue before dropping to 1 worker
        self.parsing_zero_since = None
        self.upload_zero_since = None

        # RAM estimates
        self.PARSER_RAM_MB = 100     
        self.UPLOADER_RAM_MB = 250   

    async def get_queue_sizes(self):
        try:
            p_size = await self.redis_client.llen("parse_queue")
            u_size = await self.redis_client.llen("upload_queue")
            return p_size, u_size
        except Exception as e:
            logger.error(f"[Monitorer] Redis Error: {e}")
            return 0, 0

    def get_system_stats(self):
        cpu = psutil.cpu_percent(interval=None)
        mem = psutil.virtual_memory()
        return cpu, mem.available, mem.percent

    async def socket_handler(self, sock):
        loop = asyncio.get_running_loop()
        buffer = b""
        try:
            while self.is_running:
                data = await loop.sock_recv(sock, 1024)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    msg = json.loads(line.decode('utf-8'))
                    if msg.get("type") == "report":
                        self.current_worker_counts["parser"] = msg.get("parser_count", 0)
                        self.current_worker_counts["uploader"] = msg.get("uploader_count", 0)
        finally:
            sock.close()

    async def decision_loop(self, sock):
            loop = asyncio.get_running_loop()
            
            while self.is_running:
                p_q, u_q = await self.get_queue_sizes()
                cpu_usage, ram_avail, ram_perc = self.get_system_stats()
                logger.info(f"STATS | CPU: {cpu_usage}% | RAM: {ram_perc}% | P-Queue: {p_q} | U-Queue: {u_q}")
                logger.info(f"WORKERS | Parser: {self.current_worker_counts['parser']} | Uploader: {self.current_worker_counts['uploader']}")
                
                # --- 1. Track Idle Time ---
                now = time.time()
                
                # Parser Idle Check
                if p_q == 0:
                    if self.parsing_zero_since is None: self.parsing_zero_since = now
                else:
                    self.parsing_zero_since = None
                    
                # Uploader Idle Check
                if u_q == 0:
                    if self.upload_zero_since is None: self.upload_zero_since = now
                else:
                    self.upload_zero_since = None

                # --- 2. Calculate Targets ---
                target_p = math.ceil(p_q / self.PARSING_THRESHOLD) if p_q > 0 else 1
                target_u = math.ceil(u_q / self.UPLOAD_THRESHOLD) if u_q > 0 else 1

                # Override with Idle Logic: if zero for > IDLE_DOWN_TIME, force to 1
                if self.parsing_zero_since and (now - self.parsing_zero_since > self.IDLE_DOWN_TIME):
                    target_p = 1
                if self.upload_zero_since and (now - self.upload_zero_since > self.IDLE_DOWN_TIME):
                    target_u = 1

                # --- 3. Calculate Diffs (Extra Workers) ---
                diff_p = target_p - self.current_worker_counts["parser"]
                diff_u = target_u - self.current_worker_counts["uploader"]

                # --- 4. Scale Down Suppression Logic (Cooldown) ---
                # Rule: Only allow scale down (negative diff) if:
                # A) The queue is completely empty (Immediate scale down allowed)
                # OR B) It has been at least 60 seconds since the last scale-up
                
                cooldown_seconds = 45
                time_since_last_up = now - getattr(self, 'last_scale_up_time', 0)
                
                if diff_p < 0:
                    # If queue is NOT empty and we are within cooldown, block scale down
                    if p_q > 0 and time_since_last_up < cooldown_seconds:
                        logger.info(f"[Monitorer] Parser scale-down suppressed. Cooldown: {int(cooldown_seconds - time_since_last_up)}s left.")
                        diff_p = 0
                
                if diff_u < 0:
                    # If queue is NOT empty and we are within cooldown, block scale down
                    if u_q > 0 and time_since_last_up < cooldown_seconds:
                        logger.info(f"[Monitorer] Uploader scale-down suppressed. Cooldown: {int(cooldown_seconds - time_since_last_up)}s left.")
                        diff_u = 0

                # --- 5. Constraints & Normalization ---
                if (self.current_worker_counts["parser"] + diff_p) < 1:
                    diff_p = 1 - self.current_worker_counts["parser"]
                if (self.current_worker_counts["uploader"] + diff_u) < 1:
                    diff_u = 1 - self.current_worker_counts["uploader"]

                if cpu_usage > self.CPU_CRITICAL:
                    diff_p = min(0, diff_p)
                    diff_u = min(0, diff_u)

                # RAM Normalization for scale-ups
                added_p = max(0, diff_p)
                added_u = max(0, diff_u)
                
                if added_p > 0 or added_u > 0:
                    # Update last scale up timestamp whenever we decide to add workers
                    self.last_scale_up_time = now
                    
                    needed = (added_p * self.PARSER_RAM_MB * 1048576) + (added_u * self.UPLOADER_RAM_MB * 1048576)
                    allowed = ram_avail * self.RAM_SAFE_BUFFER
                    if needed > allowed:
                        ratio = allowed / needed
                        diff_p = math.floor(diff_p * ratio) if diff_p > 0 else diff_p
                        diff_u = math.floor(diff_u * ratio) if diff_u > 0 else diff_u

                # --- 6. Send Unified Message ---
                if diff_p != 0 or diff_u != 0:
                    command = {
                        "from": "MONITORER",
                        "to": "AUTOSCALER",
                        "type": "command",
                        "parser": int(diff_p),
                        "uploader": int(diff_u)
                    }
                    try:
                        payload = (json.dumps(command) + "\n").encode('utf-8')
                        await loop.sock_sendall(sock, payload)
                        logger.info(f"[Monitorer] Scaling Signal: P:{diff_p}, U:{diff_u} (CPU:{cpu_usage}%, RAM:{ram_perc}%)")
                    except Exception as e:
                        logger.error(f"[Monitorer] Socket error: {e}")

                await asyncio.sleep(self.interval)

    async def run(self):
        while self.is_running:
            try:
                port = get_postman_port()
                sock = register_to_postman("MONITORER", port)
                await asyncio.gather(self.socket_handler(sock), self.decision_loop(sock))
            except Exception as e:
                logger.error(f"[Monitorer] Run Error: {e}")
                await asyncio.sleep(2)

async def main():
    monitorer = Monitorer(check_interval=5)
    main_task = asyncio.current_task()
    def signal_handler(*args):
        monitorer.is_running = False
        main_task.cancel()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try: signal.signal(sig, signal_handler)
        except Exception: pass
    try:
        await monitorer.run()
    except asyncio.CancelledError:
        logger.info("[Monitorer] Stopped.")
    finally:
        if monitorer.redis_client: await monitorer.redis_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())