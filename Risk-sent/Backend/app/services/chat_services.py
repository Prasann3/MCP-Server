from typing import Optional, List
from datetime import datetime
from app.db.client import mongo_client
from app.schemas.chat_schema import ChatCreate, ChatUpdate, Message
from bson import ObjectId


async def create_chat(user_id: str, payload: ChatCreate) -> dict:
    chats = mongo_client.db.chats
    doc = {
        "user_id": str(user_id),
        "title": payload.title,
        "summary": payload.summary,
        "messages": [],
        "updated_at": datetime.utcnow()
    }
    res = await chats.insert_one(doc)
    created = await chats.find_one({"_id": res.inserted_id})
    return created


async def get_chat_by_id(chat_id: str) -> Optional[dict]:
    if not ObjectId.is_valid(chat_id):
        return None
    chat = await mongo_client.db.chats.find_one({"_id": ObjectId(chat_id)} , {"messages": {"$slice": -10}})
    chat["_id"] = str(chat["_id"])
    return chat


async def list_chats(user_id: str, limit: int = 50, skip: int = 0) -> List[dict]:
    cursor = mongo_client.db.chats.find({"user_id": str(user_id)}).skip(skip).limit(limit).sort("updated_at", -1)
    return await cursor.to_list(length=limit)


async def get_message_size(chat_id : str) -> int :
    pipeline = [
    {"$match": {"_id": ObjectId(chat_id)}},
    {"$project": {
        "messagesCount": {
            "$size": {"$ifNull": ["$messages", []]}
        }
    }}
    ]
    cursor = mongo_client.db.chats.aggregate(pipeline)
    doc = await cursor.to_list(length=1)
    count = doc[0]["messagesCount"]
    return count

async def update_chat(chat_id: str, payload: ChatUpdate) -> Optional[dict]:
    if not ObjectId.is_valid(chat_id):
        return None
    update_data = {}
    if payload.title is not None:
        update_data["title"] = payload.title
    if payload.summary is not None:
        update_data["summary"] = payload.summary
    if not update_data:
        return await get_chat_by_id(chat_id)
    update_data["updated_at"] = datetime.utcnow()
    await mongo_client.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": update_data})
    return await get_chat_by_id(chat_id)


async def delete_chat(chat_id: str) -> bool:
    if not ObjectId.is_valid(chat_id):
        return False
    res = await mongo_client.db.chats.delete_one({"_id": ObjectId(chat_id)})
    return res.deleted_count == 1


async def add_message(chat_id: str, message: Message) -> Optional[dict]:
    if not ObjectId.is_valid(chat_id):
        return None
    msg_dict = message.dict()
    msg_dict["timestamp"] = message.timestamp
    res = await mongo_client.db.chats.update_one(
        {"_id": ObjectId(chat_id)},
        {
            "$push": {"messages": msg_dict},
            "$set": {"updated_at": datetime.utcnow()}
        }
    )
    if res.modified_count == 0:
        return None
    chat = await get_chat_by_id(chat_id)
    chat["_id"] = str(chat["_id"])
    return chat


async def update_message(chat_id: str, index: int, new_message: Message) -> Optional[dict]:
    chat = await get_chat_by_id(chat_id)
    if not chat:
        return None
    messages = chat.get("messages", [])
    if index < 0 or index >= len(messages):
        return None
    messages[index] = new_message.dict()
    await mongo_client.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"messages": messages, "updated_at": datetime.utcnow()}})
    chat = await get_chat_by_id(chat_id)
    chat["_id"] = str(chat["id"])
    return chat


async def delete_message(chat_id: str, index: int) -> Optional[dict]:
    chat = await get_chat_by_id(chat_id)
    if not chat:
        return None
    messages = chat.get("messages", [])
    if index < 0 or index >= len(messages):
        return None
    # remove by index
    messages.pop(index)
    await mongo_client.db.chats.update_one({"_id": ObjectId(chat_id)}, {"$set": {"messages": messages, "updated_at": datetime.utcnow()}})
    return await get_chat_by_id(chat_id)
