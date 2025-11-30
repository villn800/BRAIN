from __future__ import annotations

import io
import tempfile

from fastapi import UploadFile
from PIL import Image
from starlette.datastructures import Headers

BOOTSTRAP_USER = {
    "email": "uploader@example.com",
    "username": "uploader",
    "password": "Password123!",
}


def make_png_bytes(size: tuple[int, int] = (64, 64), color: tuple[int, int, int] = (200, 50, 50)) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", size, color=color).save(buffer, format="PNG")
    return buffer.getvalue()


def make_pdf_bytes(text: str) -> bytes:
    """Generate a tiny PDF containing the provided text."""
    buffer = io.BytesIO()
    buffer.write(b"%PDF-1.4\n")
    escaped = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream_content = f"BT\n/F1 18 Tf\n72 720 Td\n({escaped}) Tj\nET\n"
    stream_bytes = stream_content.encode("latin-1")

    objects = [
        "1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n",
        "2 0 obj\n<< /Type /Pages /Count 1 /Kids [3 0 R] >>\nendobj\n",
        "3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R >> >> >>\nendobj\n",
        f"4 0 obj\n<< /Length {len(stream_bytes)} >>\nstream\n{stream_content}endstream\nendobj\n",
        "5 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n",
    ]

    offsets = [0]
    for obj in objects:
        offsets.append(buffer.tell())
        buffer.write(obj.encode("latin-1"))

    xref_pos = buffer.tell()
    total = len(objects) + 1
    buffer.write(f"xref\n0 {total}\n".encode("latin-1"))
    buffer.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        buffer.write(f"{offset:010} 00000 n \n".encode("latin-1"))
    buffer.write(f"trailer\n<< /Size {total} /Root 1 0 R >>\n".encode("latin-1"))
    buffer.write(f"startxref\n{xref_pos}\n%%EOF".encode("latin-1"))
    return buffer.getvalue()


def make_upload_file(filename: str, content_type: str, data: bytes) -> UploadFile:
    temp_file = tempfile.SpooledTemporaryFile()
    temp_file.write(data)
    temp_file.seek(0)
    headers = Headers({"content-type": content_type})
    return UploadFile(filename=filename, file=temp_file, headers=headers)


def auth_headers(client) -> dict[str, str]:
    client.post("/api/auth/bootstrap", json=BOOTSTRAP_USER)
    token = client.post(
        "/api/auth/login",
        json={"identifier": BOOTSTRAP_USER["email"], "password": BOOTSTRAP_USER["password"]},
    ).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}