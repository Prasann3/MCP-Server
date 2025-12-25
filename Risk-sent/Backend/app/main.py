import uvicorn
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from agent_manager import RiskAgentManager 
from pydantic import BaseModel
from fastapi.responses import StreamingResponse
from app.db.client import mongo_client
from app.core.logging import logger
from app.api.v1.router import api_router

app = FastAPI(title="Risk-Sensing AI")
app.add_event_handler("startup", mongo_client.connect)
app.add_event_handler("startup", mongo_client.close)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel) :
    message : str

# Note: This will internally prepare the MCP connection

app.include_router(api_router , prefix="/api/v1")

if __name__ == "__main__":
    
    uvicorn.run(app, host="0.0.0.0", port=8000)