from fastapi import APIRouter, Depends, HTTPException, status , Request
from fastapi.responses import StreamingResponse
from typing import List
from app.schemas.chat_schema import ChatCreate, ChatOut, ChatUpdate, Message
from app.services.chat_services import create_chat, get_chat_by_id, list_chats, update_chat, delete_chat, add_message, update_message, delete_message
from app.core.auth import get_current_user
from agent_manager import agent_manager

router = APIRouter()


@router.post("/", response_model=ChatOut)
async def create_new_chat(payload: ChatCreate, user_id: str = Depends(get_current_user)):
    created = await create_chat(user_id, payload)
    return created


@router.get("/", response_model=List[ChatOut])
async def get_my_chats(user_id: str = Depends(get_current_user), limit: int = 50, skip: int = 0):
    chats = await list_chats(user_id, limit=limit, skip=skip)
    for chat in chats : 
        chat["_id"] = str(chat["_id"])
    return chats


@router.get("/{chat_id}", response_model=ChatOut)
async def get_chat(chat_id: str, user_id: str = Depends(get_current_user)):
    chat = await get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if str(chat.get("user_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    chat["_id"] = str(chat["_id"])    
    return chat


@router.put("/{chat_id}", response_model=ChatOut)
async def put_chat(chat_id: str, payload: ChatUpdate, user_id: str = Depends(get_current_user)):
    chat = await get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if str(chat.get("user_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    updated = await update_chat(chat_id, payload)
    return updated


@router.delete("/{chat_id}")
async def remove_chat(chat_id: str, user_id: str = Depends(get_current_user)):
    chat = await get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if str(chat.get("user_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    ok = await delete_chat(chat_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete")
    return {"ok": True}


@router.post("/{chat_id}/messages")
async def post_message(chat_id: str, request: Request, message: Message , user_id: str = Depends(get_current_user)):
    body = await request.json()
    doc_id = body.get("doc_id")
    print("doc_id" , doc_id)
    chat = await get_chat_by_id(chat_id)
    if not chat:
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    chat_id = chat["_id"]

    if str(chat.get("user_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")

    updated = await add_message(chat_id, message)
   
    if not updated:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to add message")
    # Ask the LLM for the response
    return StreamingResponse(
        agent_manager.run_query(message.content, chat, doc_id),
        media_type="application/json"
    )
    
   


@router.put("/{chat_id}/messages/{index}", response_model=ChatOut)
async def put_message(chat_id: str, index: int, message: Message, user_id: str = Depends(get_current_user)):
    chat = await get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if str(chat.get("user_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    updated = await update_message(chat_id, index, message)
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to update message")
    return updated


@router.delete("/{chat_id}/messages/{index}", response_model=ChatOut)
async def remove_message(chat_id: str, index: int, user_id: str = Depends(get_current_user)):
    chat = await get_chat_by_id(chat_id)
    if not chat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found")
    if str(chat.get("user_id")) != str(user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed")
    updated = await delete_message(chat_id, index)
    if not updated:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to delete message")
    return updated
