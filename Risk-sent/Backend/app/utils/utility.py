import socket
import json
import time

def register_to_postman(component_name , port):
    
    client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
       
        client_sock.connect(('127.0.0.1', port))
        message = {
            "from" : component_name ,
            "type" : "register"
        }
        
        data = json.dumps(message) + "\n"
        client_sock.sendall(data.encode('utf-8'))
        return client_sock

    except Exception as e:
        print(f"Failed to connect: {e}")
        return None


def get_postman_port() :

    with open("./app/services/port.txt" , 'r') as f :
        content = f.read().strip()
        postman_port = int(content)

    return postman_port    