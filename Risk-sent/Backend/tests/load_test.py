import asyncio
import httpx
import time
import requests

# Configuration
API_URL = "http://127.0.0.1:8000/api/v1/chats//messages"
LOGIN_URL = "http://127.0.0.1:8000/api/v1/users/login"
CONCURRENT_REQUESTS = 5
session = requests.Session()

test_cookies = {
        "token": "",
        "load_test": "true"
    }
async def send_request(client, request_id):
    payload = {
        "role" : "user",
        "content": "What are the top risks for Azure?",
        "doc_id": ""
    }
    
    # Define your cookies here
    # Example: Session ID or Auth tokens

    start_time = time.perf_counter()
    
    try:
        # Pass the cookies dictionary here
        response = await client.post(
            API_URL, 
            json=payload, 
            cookies=test_cookies, 
            timeout=60.0
        )
        
        duration = time.perf_counter() - start_time
        print(f"[Req {request_id}] Status: {response.status_code} | Time: {duration:.2f}s")
        return duration
    except Exception as e:
        print(f"[Req {request_id}] Failed: {e}")
        return None

async def main():
    # Using a single client for all requests is more efficient (connection pooling)
    # Logging in
    
    payload = {
        "email" : "" ,
        "password" : ""
    }

    response = session.post(
    url=LOGIN_URL,
    json=payload,              # auto JSON.stringify
    headers={
        "Content-Type": "application/json"
    }
    )

    if response.status_code != 200 :
        print("Entered wrong email or password , status code : " , response.status_code)
        return
    cookie = session.cookies.get_dict()
    test_cookies["token"] = cookie["token"]
    async with httpx.AsyncClient() as client:
        tasks = [send_request(client, i) for i in range(CONCURRENT_REQUESTS)]
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())