from fastapi import APIRouter
from app.api.v1.routes import users , chats , uploads

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(chats.router, prefix="/chats", tags=["Chats"])
api_router.include_router(uploads.router , prefix="/uploads" , tags=["Uploads"])
