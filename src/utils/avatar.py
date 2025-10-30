import os
import cloudinary
from fastapi import HTTPException


def set_avatar(avatar_file, user):
    if not avatar_file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    avatar_file.file.seek(0, os.SEEK_END)
    file_size = avatar_file.file.tell()
    avatar_file.file.seek(0)
    if file_size > 2 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="File too large (max 2 MB)")

    public_id = f"Web16/{user.email}"
    res = cloudinary.uploader.upload(avatar_file.file, public_id=public_id, owerite=True)
    if avatar_file.content_type == "image/svg+xml":
        res_url = cloudinary.CloudinaryImage(public_id).build_url(
            format="png", width=120, height=120, crop="fill", version=res.get("version")
        )
    else:
        res_url = cloudinary.CloudinaryImage(public_id).build_url(
            width=120, height=120, crop="fill", version=res.get("version")
        )

    return res_url