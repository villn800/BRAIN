from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .database import Base


class ItemType(str, enum.Enum):
    url = "url"
    tweet = "tweet"
    pin = "pin"
    image = "image"
    pdf = "pdf"
    note = "note"
    other = "other"


class ItemStatus(str, enum.Enum):
    ok = "OK"
    failed = "FAILED_FETCH"
    pending = "PENDING_PROCESSING"


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        Index("ix_users_created_at", "created_at"),
        Index("ix_users_updated_at", "updated_at"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    items = relationship("Item", back_populates="user", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="user", cascade="all, delete-orphan")


class Item(Base):
    __tablename__ = "items"
    __table_args__ = (
        Index("ix_items_type_created_at", "type", "created_at"),
        Index("ix_items_origin_domain", "origin_domain"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    type = Column(Enum(ItemType), nullable=False, default=ItemType.url, index=True)
    source_url = Column(Text, nullable=True)
    origin_domain = Column(String(255), nullable=True)
    title = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    text_content = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    file_path = Column(Text, nullable=True)
    original_filename = Column(String(255), nullable=True)
    content_type = Column(String(128), nullable=True)
    file_size_bytes = Column(BigInteger, nullable=True)
    status = Column(Enum(ItemStatus), nullable=False, default=ItemStatus.ok, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    user = relationship("User", back_populates="items")
    tags = relationship(
        "Tag",
        secondary="item_tags",
        back_populates="items",
        lazy="selectin",
    )


class Tag(Base):
    __tablename__ = "tags"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
        Index("ix_tags_name", "name"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    name = Column(String(64), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="tags")
    items = relationship(
        "Item",
        secondary="item_tags",
        back_populates="tags",
        lazy="selectin",
    )


class ItemTag(Base):
    __tablename__ = "item_tags"
    __table_args__ = (
        Index("ix_item_tags_tag_id", "tag_id"),
        Index("ix_item_tags_item_id", "item_id"),
    )

    item_id = Column(
        UUID(as_uuid=True),
        ForeignKey("items.id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag_id = Column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        primary_key=True,
    )
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
