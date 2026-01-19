import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.client import mongo_client
from app.api.v1.router import api_router
from agent_manager import agent_manager
from contextlib import asynccontextmanager


@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- STARTUP LOGIC ---    
    await agent_manager.initialize() 
    await mongo_client.connect()
    yield # The app stays here while running
    
    # --- SHUTDOWN LOGIC ---
    # Close the MCP Child Process (Cleanup pipes)
    await agent_manager.shutdown()
    await mongo_client.close()
    

app = FastAPI(title="Risk-Sensing AI" , lifespan = lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8080",
        "http://127.0.0.1:8080",
    ],
    allow_credentials=True, 
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router , prefix="/api/v1")

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)