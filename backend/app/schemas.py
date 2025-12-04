from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, HttpUrl, constr

from .models import ItemStatus, ItemType


class ItemBase(BaseModel):
    type: ItemType = ItemType.url
    title: str
    description: Optional[str] = None
    source_url: Optional[HttpUrl] = None
    origin_domain: Optional[str] = Field(default=None, max_length=255)
    status: ItemStatus = ItemStatus.ok
    extra: Optional[dict[str, Any]] = None


class ItemCreate(ItemBase):
    text_content: Optional[str] = None
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    original_filename: Optional[str] = Field(default=None, max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=128)
    file_size_bytes: Optional[int] = Field(default=None, ge=0)


class ItemUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ItemStatus] = None
    source_url: Optional[HttpUrl] = None
    origin_domain: Optional[str] = Field(default=None, max_length=255)
    text_content: Optional[str] = None
    file_path: Optional[str] = None
    thumbnail_path: Optional[str] = None
    original_filename: Optional[str] = Field(default=None, max_length=255)
    content_type: Optional[str] = Field(default=None, max_length=128)
    file_size_bytes: Optional[int] = Field(default=None, ge=0)


class TagOut(BaseModel):
    id: UUID
    name: str

    model_config = ConfigDict(from_attributes=True)


class TagSummary(TagOut):
    item_count: int


class TagCreate(BaseModel):
    name: constr(strip_whitespace=True, min_length=1, max_length=64)


class ItemOut(ItemBase):
    id: UUID
    thumbnail_path: Optional[str]
    file_path: Optional[str]
    original_filename: Optional[str]
    content_type: Optional[str]
    file_size_bytes: Optional[int]
    created_at: datetime
    updated_at: datetime
    text_content: Optional[str]
    tags: List[TagOut] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ItemTagsUpdate(BaseModel):
    tags: List[constr(strip_whitespace=True, min_length=1)] = Field(default_factory=list)


class UrlIngestionRequest(BaseModel):
    url: constr(strip_whitespace=True, min_length=1)
    title: Optional[str] = Field(default=None, max_length=500)
    tags: List[constr(strip_whitespace=True, min_length=1)] = Field(default_factory=list)


class HealthStatus(BaseModel):
    status: str
    db: str
    storage: str
    environment: str
    version: str
    timestamp: datetime


class UserOut(BaseModel):
    id: UUID
    email: EmailStr
    username: str
    is_admin: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


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
