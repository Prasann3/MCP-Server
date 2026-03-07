import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.client import mongo_client
from app.core.logging import logging
from app.api.v1.router import api_router
from agent_manager import agent_manager
import subprocess
import asyncio
import json
import sys
import os
from contextlib import asynccontextmanager
from app.utils.utility import get_postman_port , register_to_postman

logger = logging.getLogger("fastapi");

@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---    
    await agent_manager.initialize() 
    await mongo_client.connect()
    interpreter = sys.executable
    postman_service = subprocess.Popen(
        [interpreter , "-m" , "app.services.postman"] ,
        stdout=None,  
        stderr=None,
    )
    
    await asyncio.sleep(1);
    postman_port = get_postman_port()
    postman_socket = register_to_postman("FAST_API" , postman_port)

    if postman_socket is None :
        logger.error("Cant connect to postman")

    autoscaler = subprocess.Popen(
        [interpreter , "-m" , "app.services.autoscaler"] ,
        stdout=None,  
        stderr=None,
    )

    monitorer = subprocess.Popen(
        [interpreter , "-m" , "app.services.monitorer"] ,
        stdout=None,  
        stderr=None,
    )
    
    await asyncio.sleep(1)
    

    yield # The app stays here while running
    
    # --- SHUTDOWN LOGIC ---
    # Close the MCP Child Process (Cleanup pipes)
    await agent_manager.shutdown()
    await mongo_client.close()
    postman_service.terminate()
    postman_service.wait(timeout=10) # Ensure Postman has fully terminated before proceeding
    autoscaler.terminate()
    autoscaler.wait(timeout=10) # Ensure Autoscaler has fully terminated before proceeding
    # listener.terminate()
    # listener.wait(timeout=10) # Ensure Listener has fully terminated before proceeding
    monitorer.terminate()
    monitorer.wait(timeout=10) # Ensure Monitorer has fully terminated before proceeding
    

app = FastAPI(title="Risk-Sensing AI" , lifespan = lifespan)

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:8080")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
        FRONTEND_URL
    ],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router , prefix="/api/v1")

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)