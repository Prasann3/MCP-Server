import socket
import asyncio
import json
import os
import signal
from app.core.logging import logging

logger = logging.getLogger("postman")

class Postman:
    def __init__(self, external_socket):
        self.server_sock = external_socket
        self.routes = {}
        self.tasks = set()
        self.running = True

    def handle_exit_signal(self):
        """Signal handler for SIGTERM/SIGINT"""
        print(f"\n[Postman {os.getpid()}] Shutdown signal received. Closing router...")
        logger.info("Shutdown signal received. Stopping listener...")
        self.running = False

    async def handle_client(self, client_sock):
        loop = asyncio.get_running_loop()
        buffer = b""
        name = None

        try:
            while self.running:
                # Use a timeout-based approach or check self.running
                # sock_recv is a blocking await, so it will be interrupted by CancelledError
                data = await loop.sock_recv(client_sock, 1024)
                if not data: break
                
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    message = json.loads(line.decode('utf-8'))

                    if message.get("type") == "register":
                        name = message.get("from")
                        self.register_client(client_sock, message)
                    
                    elif "to" in message:
                        target = message["to"]
                        sender = message.get("from", "Unknown")
                        logger.info(f"Delivery: {sender} -> {target}")

                        if target not in self.routes:
                            logger.error(f"Destination {target} unreachable for {sender}")
                            continue

                        # Forward the message
                        data_to_send = (json.dumps(message) + "\n").encode('utf-8')
                        await loop.sock_sendall(self.routes[target], data_to_send)
                        
        except asyncio.CancelledError:
            logger.debug(f"Connection task for {name} cancelled.")
        except Exception as e:
            logger.error(f"[Postman] Client Error ({name}): {e}")
        finally:
            if name in self.routes: 
                del self.routes[name]
            client_sock.close()

    async def start_listening(self):
        loop = asyncio.get_running_loop()
        
        # --- Register Signals ---
        for sig in (signal.SIGTERM, signal.SIGINT):
            try:
                loop.add_signal_handler(sig, self.handle_exit_signal)
            except NotImplementedError:
                # Fallback for Windows
                signal.signal(sig, lambda s, f: self.handle_exit_signal())

        logger.info("Postman is monitoring the injected socket...")
        
        try:
            while self.running:
                try:
                    # accept() with a short timeout to check self.running
                    # Note: loop.sock_accept doesn't take a timeout, 
                    # so we wrap it in wait_for or use a small sleep.
                    client_sock, addr = await asyncio.wait_for(
                        loop.sock_accept(self.server_sock), 
                        timeout=1.0
                    )
                    logger.info(f"New connection from {addr}")
                    task = asyncio.create_task(self.handle_client(client_sock))
                    self.tasks.add(task)
                    task.add_done_callback(self.tasks.discard)
                except asyncio.TimeoutError:
                    continue # Just loop back to check self.running
                    
        except Exception as e:
            if self.running:
                logger.error(f"Listener Error: {e}")
        finally:
            await self.shutdown()

    async def shutdown(self):
        """Cleanup all resources"""
        logger.info(f"Shutting down Postman. Cleaning up {len(self.tasks)} connections...")
        self.running = False
        
        # Cancel all active client handlers
        for task in list(self.tasks):
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        self.server_sock.close()
        
        # Cleanup port file
        port_file = "./app/services/port.txt"
        if os.path.exists(port_file):
            os.remove(port_file)
            logger.info("Removed port file.")

    def register_client(self, client_sock, message):
        client = message["from"]
        self.routes[client] = client_sock
        logger.info(f"Client registered: {client}")

def get_socket():
    my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_sock.bind(('127.0.0.1', 0))
    my_sock.listen(5)
    my_sock.setblocking(False)
    
    _, port = my_sock.getsockname() 
    logger.info(f"Socket created on port {port}")

    os.makedirs("./app/services", exist_ok=True)
    with open("./app/services/port.txt", "w") as f:
        f.write(str(port))
    return my_sock

async def main():
    sock = None
    try:
        sock = get_socket()
        postman = Postman(sock)
        await postman.start_listening()
    except Exception as e:
        logger.error(f"Critical error in Postman: {e}")
    finally:
        if sock:
            sock.close()

if __name__ == "__main__":
    asyncio.run(main())