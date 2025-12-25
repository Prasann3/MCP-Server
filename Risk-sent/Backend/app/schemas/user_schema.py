from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from bson import ObjectId
from typing_extensions import Annotated
from pydantic.functional_validators import BeforeValidator


def validate_object_id(v):
    if not ObjectId.is_valid(v):
        raise ValueError("Invalid ObjectId")
    return v

PyObjectId = Annotated[str, BeforeValidator(validate_object_id)]


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = Field(None, min_length=6)


class UserInDB(UserBase):
    id: PyObjectId = Field(..., alias="_id")
    hashed_password: str

    class Config:
        json_encoders = {ObjectId: str}
        allow_population_by_field_name = True


class UserOut(BaseModel):
    id: PyObjectId = Field(alias="_id")
    email: EmailStr
    full_name: str | None = None

    model_config = {
        "populate_by_name": True,
        "validate_by_name": True,
        "json_encoders": {ObjectId: str},
    }

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
