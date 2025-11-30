"""Initial schema with users, items, tags, and item_tags tables"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "20251130_0001"
down_revision = None
branch_labels = None
depends_on = None

item_type_enum = sa.Enum(
    "url",
    "tweet",
    "pin",
    "image",
    "pdf",
    "note",
    "other",
    name="itemtype",
)

item_status_enum = sa.Enum(
    "OK",
    "FAILED_FETCH",
    "PENDING_PROCESSING",
    name="itemstatus",
)


def _uuid_type(bind):
    if bind.dialect.name == "postgresql":
        return postgresql.UUID(as_uuid=True)
    return sa.String(length=36)


def upgrade() -> None:
    bind = op.get_bind()
    uuid_type = _uuid_type(bind)

    if bind.dialect.name == "postgresql":
        item_type_enum.create(bind, checkfirst=True)
        item_status_enum.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_admin", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
        sa.UniqueConstraint("username", name="uq_users_username"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)
    op.create_index("ix_users_username", "users", ["username"], unique=False)
    op.create_index("ix_users_created_at", "users", ["created_at"], unique=False)
    op.create_index("ix_users_updated_at", "users", ["updated_at"], unique=False)

    op.create_table(
        "items",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("type", item_type_enum, nullable=False),
        sa.Column("source_url", sa.Text(), nullable=True),
        sa.Column("origin_domain", sa.String(length=255), nullable=True),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("text_content", sa.Text(), nullable=True),
        sa.Column("thumbnail_path", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("original_filename", sa.String(length=255), nullable=True),
        sa.Column("content_type", sa.String(length=128), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("status", item_status_enum, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_items_user_id", "items", ["user_id"], unique=False)
    op.create_index("ix_items_type", "items", ["type"], unique=False)
    op.create_index("ix_items_status", "items", ["status"], unique=False)
    op.create_index("ix_items_created_at", "items", ["created_at"], unique=False)
    op.create_index("ix_items_origin_domain", "items", ["origin_domain"], unique=False)
    op.create_index("ix_items_type_created_at", "items", ["type", "created_at"], unique=False)

    op.create_table(
        "tags",
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("user_id", uuid_type, nullable=False),
        sa.Column("name", sa.String(length=64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_tag_user_name"),
    )
    op.create_index("ix_tags_name", "tags", ["name"], unique=False)
    op.create_index("ix_tags_user_id", "tags", ["user_id"], unique=False)

    op.create_table(
        "item_tags",
        sa.Column("item_id", uuid_type, nullable=False),
        sa.Column("tag_id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=False), nullable=False),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("item_id", "tag_id"),
    )
    op.create_index("ix_item_tags_tag_id", "item_tags", ["tag_id"], unique=False)
    op.create_index("ix_item_tags_item_id", "item_tags", ["item_id"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()

    op.drop_index("ix_item_tags_item_id", table_name="item_tags")
    op.drop_index("ix_item_tags_tag_id", table_name="item_tags")
    op.drop_table("item_tags")
    op.drop_index("ix_tags_user_id", table_name="tags")
    op.drop_index("ix_tags_name", table_name="tags")
    op.drop_table("tags")
    op.drop_index("ix_items_type_created_at", table_name="items")
    op.drop_index("ix_items_origin_domain", table_name="items")
    op.drop_index("ix_items_created_at", table_name="items")
    op.drop_index("ix_items_status", table_name="items")
    op.drop_index("ix_items_type", table_name="items")
    op.drop_index("ix_items_user_id", table_name="items")
    op.drop_table("items")
    op.drop_index("ix_users_updated_at", table_name="users")
    op.drop_index("ix_users_created_at", table_name="users")
    op.drop_index("ix_users_username", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    if bind.dialect.name == "postgresql":
        item_type_enum.drop(bind, checkfirst=True)
        item_status_enum.drop(bind, checkfirst=True)
