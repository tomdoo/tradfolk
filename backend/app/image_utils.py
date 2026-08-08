import os
import uuid
from pathlib import Path

import pyvips
from werkzeug.datastructures import FileStorage


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "/app/uploads")
PROPOSALS_SUBDIR = "proposals"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
MAX_DIMENSION = 2000

ALLOWED_MIME_TYPES = frozenset({
    "image/jpeg",
    "image/jpg",
    "image/png",
    "image/webp",
    "image/gif",
    "image/bmp",
    "image/tiff",
})


class ImageUploadError(Exception):
    pass


def _load_image(data: bytes, content_type: str) -> pyvips.Image:
    """Load an image, including all frames for animated GIF/WebP."""

    try:
        if content_type == "image/gif":
            return pyvips.Image.gifload_buffer(
                data,
                n=-1,
                access="sequential",
            )

        if content_type == "image/webp":
            return pyvips.Image.webpload_buffer(
                data,
                n=-1,
                access="sequential",
            )

        return pyvips.Image.new_from_buffer(
            data,
            "",
            access="sequential",
        )

    except pyvips.Error as exc:
        raise ImageUploadError("Impossible de lire l'image.") from exc


def _resize_image(image: pyvips.Image) -> pyvips.Image:
    """Downscale an image without ever upscaling it."""

    # For animated images, image.height is the total height
    # of all frames stacked vertically.
    page_height = _get_page_height(image)

    width = image.width
    height = page_height

    scale = min(
        1.0,
        MAX_DIMENSION / width,
        MAX_DIMENSION / height,
    )

    if scale >= 1.0:
        return image

    image = image.resize(
        scale,
        vscale=scale,
        kernel="lanczos",
    )

    # Preserve the frame height after resizing.
    if page_height != image.height:
        resized_page_height = round(page_height * scale)
        image.set_type(pyvips.GValue.gint_type, "page-height", resized_page_height)

    return image

def _get_page_height(image: pyvips.Image) -> int:
    if image.get_typeof("page-height") != 0:
        return image.get("page-height")

    return image.height

def save_proposal_image(file: FileStorage) -> str:
    """Validate, resize, convert to WebP and persist an uploaded image."""

    # Validate MIME type
    content_type = (file.content_type or "").lower().split(";")[0].strip()

    if content_type not in ALLOWED_MIME_TYPES:
        raise ImageUploadError(
            "Type de fichier non supporté. "
            "Formats acceptés : JPEG, PNG, WebP, GIF, BMP, TIFF."
        )

    # Read uploaded data
    data = file.read()

    if len(data) > MAX_FILE_SIZE:
        raise ImageUploadError(
            f"Image trop volumineuse. "
            f"Taille maximale : {MAX_FILE_SIZE // (1024 * 1024)} Mo."
        )

    # Decode image
    image = _load_image(data, content_type)

    # Resize if necessary
    image = _resize_image(image)

    # Create destination directory
    save_dir = Path(UPLOAD_DIR) / PROPOSALS_SUBDIR
    save_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    filename = f"{uuid.uuid4()}.webp"
    file_path = save_dir / filename

    try:
        page_height = _get_page_height(image)

        image.webpsave(
            str(file_path),
            Q=85,
            effort=6,
            page_height=page_height,
        )
    except pyvips.Error as exc:
        raise ImageUploadError(
            "Impossible d'enregistrer l'image."
        ) from exc

    return f"/uploads/{PROPOSALS_SUBDIR}/{filename}"
