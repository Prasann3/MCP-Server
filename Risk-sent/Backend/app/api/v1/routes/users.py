from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from app.schemas.user_schema import UserCreate, UserOut, UserUpdate, Token
from app.services.user_service import create_user, authenticate_user, get_user_by_id, list_users, update_user, delete_user
from app.core.auth import create_access_token, get_current_user
from typing import List

router = APIRouter()


@router.post("/", response_model=UserOut)
async def register_user(data: UserCreate):
    try:
        created = await create_user(data)
        created["_id"] = str(created["_id"])
        return created
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/login", response_model=Token)
async def login_user(response: Response, data: UserCreate):
    # re-using UserCreate for simple email + password payload
    user = await authenticate_user(data.email, data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user.get("_id")))
    # set cookie — in production set secure=True and samesite properly
    response.set_cookie(key="access_token", value=token, httponly=True, samesite="Lax")
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout")
async def logout(response: Response):
    response.delete_cookie("access_token")
    return {"ok": True}


@router.get("/me", response_model=UserOut)
async def get_me(user_id: str = Depends(get_current_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.get("/", response_model=List[UserOut])
async def get_users(limit: int = 50, skip: int = 0, _: str = Depends(get_current_user)):
    users = await list_users(limit=limit, skip=skip)
    return users


@router.get("/{user_id}", response_model=UserOut)
async def get_user(user_id: str, _: str = Depends(get_current_user)):
    user = await get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    print(user["_id"])    
    return user


@router.put("/{user_id}", response_model=UserOut)
async def put_user(user_id: str, payload: UserUpdate, _: str = Depends(get_current_user)):
    updated = await update_user(user_id, payload)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return updated


@router.delete("/{user_id}")
async def remove_user(user_id: str, _: str = Depends(get_current_user)):
    ok = await delete_user(user_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return {"ok": True}
