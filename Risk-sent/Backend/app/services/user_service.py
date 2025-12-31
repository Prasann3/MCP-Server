from typing import Optional, List
from app.db.client import mongo_client
from app.schemas.user_schema import UserCreate, UserInDB, UserOut, UserUpdate
from app.utils.hash import hash_password, verify_password
from bson import ObjectId


async def create_user(user: UserCreate) -> dict:
    users = mongo_client.db.users
    existing = await users.find_one({"email": user.email})
    if existing:
        raise ValueError("User with that email already exists")
    hashed = hash_password(user.password)
    doc = {"email": user.email, "full_name": user.full_name, "hashed_password": hashed}
    print(doc["full_name"])
    res = await users.insert_one(doc)
    created = await users.find_one({"_id": res.inserted_id})
    return created


async def get_user_by_email(email: str) -> Optional[dict]:
    return await mongo_client.db.users.find_one({"email": email})


async def get_user_by_id(user_id: str) -> Optional[dict]:
    if not ObjectId.is_valid(user_id):
        return None
    user = await mongo_client.db.users.find_one({"_id": ObjectId(user_id)})
    user["_id"] = str(user["_id"])
    print(user["_id"])
    return user


async def list_users(limit: int = 50, skip: int = 0) -> List[dict]:
    cursor = mongo_client.db.users.find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)

    for user in users : 
        user["_id"] = str(user["_id"])
    return users    


async def update_user(user_id: str, payload: UserUpdate) -> Optional[dict]:
    update_data = {}
    if payload.full_name is not None:
        update_data["full_name"] = payload.full_name
    if payload.password is not None:
        update_data["hashed_password"] = hash_password(payload.password)
    if not update_data:
        return await get_user_by_id(user_id)
    await mongo_client.db.users.update_one({"_id": ObjectId(user_id)}, {"$set": update_data})
    return await get_user_by_id(user_id)


async def delete_user(user_id: str) -> bool:
    res = await mongo_client.db.users.delete_one({"_id": ObjectId(user_id)})
    return res.deleted_count == 1


async def authenticate_user(email: str, password: str) -> Optional[dict]:
    user = await get_user_by_email(email)
    if not user:
        return None
    if not verify_password(password, user.get("hashed_password")):
        return None
    return user
