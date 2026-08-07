import io
import os
import uuid
from pathlib import Path

from PIL import Image, ImageSequence, UnidentifiedImageError
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


def _normalize_mode(frame: Image.Image) -> Image.Image:
    if frame.mode in ("RGBA", "LA", "PA"):
        return frame.convert("RGBA")
    return frame.convert("RGB")


def _downscale_only(frame: Image.Image) -> Image.Image:
    w, h = frame.size
    if w > MAX_DIMENSION or h > MAX_DIMENSION:
        frame = frame.copy()
        frame.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
    return frame


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
        probe = Image.open(io.BytesIO(data))
        probe.verify()
    except (UnidentifiedImageError, Exception) as exc:
        raise ImageUploadError("Impossible de lire l'image.") from exc

    img = Image.open(io.BytesIO(data))

    save_dir = Path(UPLOAD_DIR) / PROPOSALS_SUBDIR
    save_dir.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4()}.webp"
    file_path = save_dir / filename

    is_animated = bool(getattr(img, "is_animated", False) and getattr(img, "n_frames", 1) > 1)

    if is_animated:
        frames: list[Image.Image] = []
        durations: list[int] = []

        for frame in ImageSequence.Iterator(img):
            processed = _downscale_only(_normalize_mode(frame))
            frames.append(processed)
            durations.append(int(frame.info.get("duration", 100)))

        first, rest = frames[0], frames[1:]
        first.save(
            file_path,
            format="WEBP",
            save_all=True,
            append_images=rest,
            duration=durations,
            loop=int(img.info.get("loop", 0)),
            quality=85,
            method=6,
        )
    else:
        still = _downscale_only(_normalize_mode(img))
        still.save(file_path, format="WEBP", quality=85, method=6)

    return f"/uploads/{PROPOSALS_SUBDIR}/{filename}"
