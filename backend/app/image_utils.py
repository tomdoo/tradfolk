import io
import os
import uuid
from pathlib import Path

from PIL import Image, UnidentifiedImageError
from werkzeug.datastructures import FileStorage

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
PROPOSALS_SUBDIR = "proposals"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DIMENSION = 2000
ALLOWED_MIME_TYPES = frozenset(
    {
        "image/jpeg",
        "image/jpg",
        "image/png",
        "image/webp",
        "image/gif",
        "image/bmp",
        "image/tiff",
    }
)


class ImageUploadError(Exception):
    pass


def save_proposal_image(file: FileStorage) -> str:
    """Validate, convert to WebP, resize and persist an uploaded image.

    Returns the public relative path, e.g. ``/uploads/proposals/<uuid>.webp``.
    Raises :exc:`ImageUploadError` for invalid or oversized input.
    """
    content_type = (file.content_type or "").lower().split(";")[0].strip()
    if content_type not in ALLOWED_MIME_TYPES:
        raise ImageUploadError(
            "Type de fichier non supporté. Formats acceptés : JPEG, PNG, WebP, GIF, BMP."
        )

    data = file.read()
    if len(data) > MAX_FILE_SIZE:
        raise ImageUploadError(
            f"Image trop volumineuse. Taille maximale : {MAX_FILE_SIZE // (1024 * 1024)} Mo."
        )

    try:
        # verify() checks the file is not truncated/corrupt
        probe = Image.open(io.BytesIO(data))
        probe.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageUploadError("Impossible de lire l'image.") from exc

    # Reopen: verify() exhausts/closes the internal stream
    img = Image.open(io.BytesIO(data))

    # Preserve transparency for formats that support it, otherwise use RGB
    if img.mode in ("RGBA", "LA", "PA"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # Downscale only — never upscale
    w, h = img.size
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

    save_dir = Path(UPLOAD_DIR) / PROPOSALS_SUBDIR
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.webp"
    file_path = save_dir / filename
    img.save(file_path, format="WEBP", quality=85, method=6)

    return f"/uploads/{PROPOSALS_SUBDIR}/{filename}"
