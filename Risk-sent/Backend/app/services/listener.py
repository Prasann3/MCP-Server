import socket
import json
import os
import time

def start_listener():
    # 1. Find the Postman
    try:
        with open("./app/services/port.txt", "r") as f:
            port = int(f.read().strip())
    except FileNotFoundError:
        print("[Listener] Error: postman_port.txt not found. Is Postman running?")
        return

    # 2. Connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.connect(('127.0.0.1', port))
        print(f"[Listener] Connected to Postman on port {port}")

        # 3. Register our name
        message = {"from": "listener", "type": "register"}
        sock.sendall((json.dumps(message) + "\n").encode())
        print("[Listener] Registered as 'listener'. Waiting for messages...")

        # 4. Stay alive and listen
        buffer = b""
        while True:
            data = sock.recv(1024)
            if not data:
                print("[Listener] Postman closed the connection.")
                break
            
            buffer += data
            while b"\n" in buffer:
                line, buffer = buffer.split(b"\n", 1)
                message = json.loads(line.decode())
                print(f"\n[RECEIVED DATA]: {message}")
                
    except Exception as e:
        print(f"[Listener] Error: {e}")
    finally:
        sock.close()

if __name__ == "__main__":
    start_listener()