import socket
import asyncio
import json
import os
import signal
import subprocess
import sys
import platform
from app.core.logging import logging
from app.utils.utility import get_postman_port , register_to_postman

logger = logging.getLogger("autoscaler")
interpreter = sys.executable

class Autoscaler:
    def __init__(self , min_workers=1):
        self.parsing_worker_path = "app.workers.parsing_worker"
        self.upload_worker_path = "app.workers.upload_worker"
        self.min_workers = min_workers
        
        # Store Process Objects for safe killing on Windows
        self.parsing_worker_procs = []
        self.upload_worker_procs = []
        self.is_running = True

    def spawn_workers(self, parsing_count, upload_count):
        """Starts worker processes and stores their objects."""
        if parsing_count > 0 :
            for _ in range(parsing_count):
                try:
                    proc = subprocess.Popen([interpreter, "-m", self.parsing_worker_path])
                    self.parsing_worker_procs.append(proc)
                    logger.info(f"[Autoscaler] Spawned Parsing Worker PID: {proc.pid}")
                except Exception as e:
                    logger.error(f"[Autoscaler] Parsing spawn error: {e}")
        
        if upload_count > 0 :
            for _ in range(upload_count):
                try:
                    proc = subprocess.Popen([interpreter, "-m", self.upload_worker_path])
                    self.upload_worker_procs.append(proc)
                    logger.info(f"[Autoscaler] Spawned Upload Worker PID: {proc.pid}")
                except Exception as e:
                    logger.error(f"[Autoscaler] Upload spawn error: {e}")

    def stop_and_kill_all(self):
        """Emergency cleanup: Works on Windows and Linux."""
        self.is_running = False
        all_procs = self.parsing_worker_procs + self.upload_worker_procs
        logger.warning(f"[Autoscaler] Shutdown: Purging {len(all_procs)} workers...")
        
        for proc in all_procs:
            try:
                # .kill() is cross-platform (SIGKILL on Unix, TerminateProcess on Windows)
                proc.kill() 
                proc.wait(timeout=5) # Wait for process to terminate, with timeout
                logger.info(f"[Autoscaler] Force killed worker PID: {proc.pid}")
            except Exception:
                pass
        
        self.parsing_worker_procs.clear()
        self.upload_worker_procs.clear()

    async def kill_workers(self, parsing_count, upload_count):
        """Graceful kill logic."""
        # Parsing cleanup
        if parsing_count < 0 :
            parsing_count = abs(parsing_count)
            for _ in range(min(parsing_count, len(self.parsing_worker_procs))):
                proc = self.parsing_worker_procs.pop(0)
                logger.info(f"[Autoscaler] Terminating Parsing Worker PID: {proc.pid}")
                proc.terminate() # Sends SIGTERM on Unix, TerminateProcess on Windows

        # Upload cleanup
        if upload_count < 0 :
            upload_count = abs(upload_count)
            for _ in range(min(upload_count, len(self.upload_worker_procs))):
                proc = self.upload_worker_procs.pop(0)
                logger.info(f"[Autoscaler] Terminating Upload Worker PID: {proc.pid}")
                proc.terminate() # Sends SIGTERM on Unix, TerminateProcess on Windows

    async def socket_handler(self, sock):
        """Listens to Postman for scaling commands."""
        loop = asyncio.get_running_loop()
        buffer = b""
        try:
            while self.is_running:
                data = await loop.sock_recv(sock, 1024)
                if not data: break
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    messsage = json.loads(line.decode('utf-8'))
                    
                    action = messsage.get("action")
                    p_val = messsage.get("parser")
                    u_val = messsage.get("uploader")
                    logger.info(f"[Autoscaler] Received command: {action} | Parser: {p_val} | Uploader: {u_val}")
                    self.spawn_workers(p_val, u_val)
                    await self.kill_workers(p_val, u_val)

                    message = {
                        "from" : "AUTOSCALER" ,
                        "to" : "MONITORER" ,
                        "type" : "report" ,
                        "uploader_count" : len(self.upload_worker_procs) ,
                        "parser_count" : len(self.parsing_worker_procs)
                    }

                    data_to_send = (json.dumps(message) + "\n").encode('utf-8')
                    await loop.sock_sendall(sock, data_to_send)

        finally:
            sock.close()

    async def connect_and_listen(self):
        loop = asyncio.get_running_loop()
        while self.is_running:
            try:
                
                port = get_postman_port()
                sock = register_to_postman("AUTOSCALER", port)
        
                await self.socket_handler(sock)
            except (FileNotFoundError, ConnectionRefusedError):
                await asyncio.sleep(2)
            except Exception as e:
                logger.error(f"[Autoscaler] Connection error: {e}")
                await asyncio.sleep(2)

    async def health_check_loop(self):
        """Verifies if subprocesses are still alive."""
        while self.is_running:
            # Filter out dead processes using .poll() 
            self.parsing_worker_procs = [p for p in self.parsing_worker_procs if p.poll() is None]
            self.upload_worker_procs = [p for p in self.upload_worker_procs if p.poll() is None]
            
            total = len(self.parsing_worker_procs) + len(self.upload_worker_procs)
            if total < self.min_workers:
                self.spawn_workers(self.min_workers , self.min_workers)
            
            await asyncio.sleep(7)

    async def run(self):
        self.spawn_workers(self.min_workers, self.min_workers)
        await asyncio.gather(
            self.connect_and_listen(),
            self.health_check_loop()
        )

# --- Windows-Compatible Execution Wrapper ---

async def main():
    scaler = Autoscaler()
    main_task = asyncio.current_task()

    # Bridge for Windows: loop.add_signal_handler doesn't work on Win
    def signal_handler(*args):
        main_task.cancel()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            signal.signal(sig, signal_handler)
        except Exception:
            pass

    try:
        await scaler.run()
    except asyncio.CancelledError:
        logger.info("[Autoscaler] Received stop signal.")
    finally:
        # Crucial: This kills the workers before the script exits
        scaler.stop_and_kill_all()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass # Clean exit on Ctrl+C