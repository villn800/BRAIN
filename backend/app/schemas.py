from __future__ import annotations

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, HttpUrl

from .models import ItemStatus, ItemType


class ItemBase(BaseModel):
    type: ItemType = ItemType.url
    title: str
    description: Optional[str] = None
    source_url: Optional[HttpUrl] = None


class ItemCreate(ItemBase):
    pass


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class TagOut(BaseModel):
    id: UUID
    name: str

    class Config:
        orm_mode = True


class ItemOut(ItemBase):
    id: UUID
    origin_domain: Optional[str]
    thumbnail_path: Optional[str]
    file_path: Optional[str]
    status: ItemStatus
    created_at: datetime
    updated_at: datetime
    tags: List[TagOut] = []

    class Config:
        orm_mode = True


class HealthStatus(BaseModel):
    status: str
    db: str
    storage: str


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class BootstrapUserRequest(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    identifier: str
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
