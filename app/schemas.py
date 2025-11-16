import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=150)
    email: EmailStr


class UserCreate(UserBase):
    password: str = Field(..., min_length=6)


class UserRead(UserBase):
    id: int
    is_active: bool
    is_superuser: bool
    create_at: datetime.datetime

    class Config:
        orm_mode = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None


class TokenData(BaseModel):
    username: Optional[str] = None


class CameraBase(BaseModel):
    camera_id: str = Field(..., max_length=100)
    name: str = Field(..., max_length=255)


class CameraCreate(CameraBase):
    pass


class CameraUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class CameraRead(CameraBase):
    id: int
    owner_id: int
    is_deleted: bool
    created_at: datetime.datetime
    updated_at: datetime.datetime

    class Config:
        orm_mode = True
