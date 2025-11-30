from __future__ import annotations

from uuid import uuid4

from app import models, schemas
from app.database import SessionLocal
from app.services import items_service


def _create_user(db) -> models.User:
    user = models.User(
        email=f"user-{uuid4().hex[:6]}@example.com",
        username=f"user_{uuid4().hex[:6]}",
        password_hash="hash",
        is_admin=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def test_create_item_normalizes_paths_and_domain(app_client_factory) -> None:
    _, storage_root = app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        absolute_file = storage_root / "uploads" / "images" / "asset.jpg"
        absolute_thumb = storage_root / "uploads" / "images" / "asset_thumb.jpg"
        item = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="Example",
                type=models.ItemType.image,
                source_url="https://Example.com/path",
                description="Item for testing",
                file_path=str(absolute_file),
                thumbnail_path=str(absolute_thumb),
                original_filename=" Asset.JPG ",
                content_type=" image/jpeg ",
                file_size_bytes=1024,
            ),
        )
        assert item.origin_domain == "example.com"
        assert item.file_path and item.file_path.startswith("uploads/images/")
        assert item.thumbnail_path and item.thumbnail_path.startswith("uploads/images/")
        assert item.original_filename == "Asset.JPG"
        assert item.content_type == "image/jpeg"
        assert item.file_size_bytes == 1024
    finally:
        db.close()


def test_item_crud_flow(app_client_factory) -> None:
    app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        first = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="URL Item",
                type=models.ItemType.url,
                source_url="https://example.com/article",
            ),
        )
        second = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(
                title="Image Item",
                type=models.ItemType.image,
                status=models.ItemStatus.pending,
            ),
        )

        listed = items_service.list_items(
            db,
            user,
            item_type=models.ItemType.url,
        )
        assert [item.id for item in listed] == [first.id]

        fetched = items_service.get_item(db, user, first.id)
        assert fetched is not None
        assert fetched.title == "URL Item"

        updated = items_service.update_item(
            db,
            first,
            schemas.ItemUpdate(
                title="Updated", source_url="https://sub.domain.dev/page"
            ),
        )
        assert updated.title == "Updated"
        assert updated.origin_domain == "sub.domain.dev"

        items_service.delete_item(db, second)
        assert items_service.get_item(db, user, second.id) is None
    finally:
        db.close()


def test_set_item_tags_is_idempotent_and_scoped(app_client_factory) -> None:
    app_client_factory()
    db = SessionLocal()
    try:
        user = _create_user(db)
        other_user = _create_user(db)
        item = items_service.create_item(
            db,
            user,
            schemas.ItemCreate(title="Tagged", type=models.ItemType.other),
        )

        updated = items_service.set_item_tags(db, user, item, ["Design", " UX "])
        assert {tag.name for tag in updated.tags} == {"Design", "UX"}

        repeat = items_service.set_item_tags(
            db,
            user,
            item,
            ["design", "ux", "New"],
        )
        assert {tag.name for tag in repeat.tags} == {"Design", "UX", "New"}
        assert db.query(models.Tag).filter(models.Tag.user_id == user.id).count() == 3

        trimmed = items_service.set_item_tags(db, user, item, ["New"])
        assert {tag.name for tag in trimmed.tags} == {"New"}

        other_item = items_service.create_item(
            db,
            other_user,
            schemas.ItemCreate(title="Other", type=models.ItemType.note),
        )
        other_updated = items_service.set_item_tags(db, other_user, other_item, ["Design"])
        assert {tag.user_id for tag in other_updated.tags} == {other_user.id}
    finally:
        db.close()