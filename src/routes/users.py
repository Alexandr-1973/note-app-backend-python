import os
import pickle
import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File, HTTPException, Response, Form
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.database.models import User
# from src.repository.users import get_user_by_email
from src.schemas import UserResponse, UserSchema, UserUpdateSchema
from src.services.auth import auth_service
# from src.conf.config import config
from src.repository import users as repositories_users
from fastapi import Request
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/users", tags=["users"])
# cloudinary.config(
#     cloud_name=config.CLOUDINARY_NAME,
#     api_key=config.CLOUDINARY_API_KEY,
#     api_secret=config.CLOUDINARY_API_SECRET,
#     secure=True,
# )



@router.get("/me")
async def get_current_user(
    request: Request, db: AsyncSession = Depends(get_db)
):
    access_token = request.cookies.get("accessToken")
    print(access_token)

    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        email = await auth_service.decode_token(access_token, expected_scope="access_token")
        user = await repositories_users.get_user_by_email(email, db)
        # user_data = {
        #     "username": user.username,
        #     "email": user.email,
        #     "avatar": user.avatar
        # }
        return {
            "username": user.username,
            "email": user.email,
            "avatar": user.avatar
        }
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired access token")



# @router.patch("/me")
# async def patch_user(request: Request, body: UserSchema, db:AsyncSession=Depends(get_db)):
#     access_token = request.cookies.get("accessToken")
#     if not access_token:
#         raise HTTPException(status_code=401, detail="Not authenticated")
#     try:
#         user = await repositories_users.get_user_by_email(body.email,db)
#         user.username=body.username
#         await db.commit()
#         await db.refresh(user)
#
#         return user
#     except HTTPException:
#         raise HTTPException(status_code=401, detail="Invalid refresh token")

# @router.patch("/me")
# async def patch_user(request: Request, body: UserUpdateSchema, db: AsyncSession = Depends(get_db)):
#     access_token = request.cookies.get("accessToken")
#     if not access_token:
#         raise HTTPException(status_code=401, detail="Not authenticated")
#
#
#     try:
#         email = await auth_service.decode_token(access_token, expected_scope="access_token")
#     except HTTPException:
#         raise HTTPException(status_code=401, detail="Invalid access token")
#
#     user = await repositories_users.get_user_by_email(email, db)
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#
#
#     if body.username:
#         user.username = body.username
#     if body.avatar:
#         user.avatar = body.avatar
#
#
#     await db.commit()
#     await db.refresh(user)
#
#     return {
#         "username": user.username,
#         "email": user.email,
#         "avatar": user.avatar
#     }


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
        print("Receive file:", avatar_file.filename)

        contents = await avatar_file.read()
        upload_dir = "uploads/avatars"
        os.makedirs(upload_dir, exist_ok=True)

        file_path = os.path.join(upload_dir, f"{user.id}_{avatar_file.filename}")
        print("Save file to:", file_path)

        with open(file_path, "wb") as f:
            f.write(contents)
        # user.avatar = file_path

    await db.commit()
    await db.refresh(user)

    return {
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar,
    }


@router.patch(
    "/avatar",
    response_model=UserResponse)
async def get_current_user(
    file: UploadFile = File(),
    user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_db),
):
    public_id = f"Web16/{user.email}"
    res = cloudinary.uploader.upload(file.file, public_id=public_id, owerite=True)
    res_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", version=res.get("version")
    )
    user = await repositories_users.update_avatar_url(user.email, res_url, db)
    auth_service.cache.set(user.email, pickle.dumps(user))
    auth_service.cache.expire(user.email, 300)
    return user