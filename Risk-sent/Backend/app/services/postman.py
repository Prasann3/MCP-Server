import socket
import asyncio
import json
from app.core.logging import logging

logger = logging.getLogger("postman")

class Postman:
    def __init__(self, external_socket):
       
        self.server_sock = external_socket
        self.routes = {}

    async def handle_client(self, client_sock):
        loop = asyncio.get_running_loop()
        buffer = b""
        name = None

        try:
            while True:
                data = await loop.sock_recv(client_sock, 1024)
                if not data: break
                
                buffer += data
                while b"\n" in buffer:
                    line, buffer = buffer.split(b"\n", 1)
                    message = json.loads(line.decode('utf-8'))

                    if message["type"] == "register" :
                        self.register_client(client_sock , message)
                        name = message["from"]
                    
                    elif "to" in message:
                        target = message["to"]
                        logger.info(f"delivery request arrived from {message["from"]} to {message["to"]}")

                        if target not in self.routes :
                            logger.error(f"Message from {name} cant be delivered as destination {target} is not reachable from postman")
                            continue

                        if target in self.routes:
                            packet =  message
                            data_to_send = (json.dumps(packet) + "\n").encode('utf-8')
                            await loop.sock_sendall(self.routes[target], data_to_send)
        except Exception as e:
            logger.error(f"[Postman] Connection error: {e.with_traceback()}")
        finally:
            if name in self.routes: del self.routes[name]
            client_sock.close()

    async def start_listening(self):
        loop = asyncio.get_running_loop()
        logger.info("Postman is now monitoring the injected socket...")
        
        while True:
            client_sock, addr = await loop.sock_accept(self.server_sock)
            logger.info("New connection request arrived")
            print(client_sock)
            asyncio.create_task(self.handle_client(client_sock))


    def register_client(self , client_sock , message) :
         
         client = message["from"]
         self.routes[client] = client_sock
         logger.info(f"New Client registered : {message["from"]}")


# --- YOUR MANUAL SOCKET CREATION ---

def get_socket():
    # 1. You create it
    my_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    my_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    # 2. You bind it to Port 0 (Dynamic)
    my_sock.bind(('127.0.0.1', 0))
    my_sock.listen(5)
    
    # 3. CRITICAL: You must set it to non-blocking for asyncio!
    my_sock.setblocking(False)
    
    _, port = my_sock.getsockname() 
    logger.info(f"Socket created on port {port}")

    with open("./app/services/port.txt", "w") as f:
        f.write(str(port))
    logger.info("Created the port file")    
    return my_sock

async def main():
    # Call your own socket logic
    sock = get_socket()
  
    postman = Postman(sock)
    await postman.start_listening()


if __name__ == "__main__":
    asyncio.run(main())