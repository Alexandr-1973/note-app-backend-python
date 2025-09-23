import os
import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File, HTTPException, Form
)
from sqlalchemy.ext.asyncio import AsyncSession
from src.conf.config import config
from src.database.db import get_db
from src.services.auth import auth_service
from src.repository import users as repositories_users
from fastapi import Request


router = APIRouter(prefix="/users", tags=["users"])
cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True,
)


@router.get("/me")
async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("accessToken")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        email = await auth_service.decode_token(access_token, expected_scope="access_token")
        user = await repositories_users.get_user_by_email(email, db)

        return {
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar
        }
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")


@router.patch("/me")
async def patch_user(
    request: Request,
    username: str = Form(None),
    avatar_file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db),
):
    access_token = request.cookies.get("accessToken")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        email = await auth_service.decode_token(access_token, expected_scope="access_token")
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid access token")

    user = await repositories_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if username:
        user.username = username

    if avatar_file:
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
        # res_url = cloudinary.CloudinaryImage(public_id).build_url( version=res.get("version"))
        user.avatar = res_url

    await db.commit()
    await db.refresh(user)

    return {
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
    }

