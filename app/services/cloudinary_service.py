import logging
import re
from typing import Optional

import cloudinary
import cloudinary.uploader

from app.config import settings

logger = logging.getLogger(__name__)

cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True,
)


def upload_image(file_path: str, folder: str = "emenu") -> str:
    result = cloudinary.uploader.upload(file_path, folder=folder)
    return result["secure_url"]


def upload_image_bytes(file_bytes: bytes, folder: str = "emenu") -> str:
    result = cloudinary.uploader.upload(file_bytes, folder=folder)
    return result["secure_url"]


def delete_image(url: str) -> bool:
    if not url or "cloudinary.com" not in url:
        return False
    try:
        match = re.search(r"/upload/(?:v\d+/)?(.+?)(?:\.\w+)?$", url)
        if not match:
            return False
        public_id = match.group(1)
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        logger.error(f"Failed to delete Cloudinary image: {e}")
        return False
