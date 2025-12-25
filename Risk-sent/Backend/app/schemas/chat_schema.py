from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from bson import ObjectId
from app.schemas.user_schema import PyObjectId


class Message(BaseModel):
    role: str = Field(..., description="'user' or 'assistant' or other roles")
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    tool_calls: Optional[List[str]] = None


class ChatBase(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None


class ChatCreate(ChatBase):
    pass


class ChatUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None


class ChatInDB(ChatBase):
    id: PyObjectId = Field(..., alias="_id")
    user_id: str
    messages: List[Message] = []
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        allow_population_by_field_name = True


class ChatOut(ChatBase):
    id: PyObjectId = Field(..., alias="_id")
    user_id: str
    messages: List[Message]
    updated_at: datetime

    class Config:
        json_encoders = {ObjectId: str, datetime: lambda v: v.isoformat()}
        allow_population_by_field_name = True
