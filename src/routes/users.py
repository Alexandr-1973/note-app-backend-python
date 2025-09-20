import pickle
import cloudinary
import cloudinary.uploader
from fastapi import (
    APIRouter,
    Depends,
    UploadFile,
    File, HTTPException, Response
)
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.database.models import User
# from src.repository.users import get_user_by_email
from src.schemas import UserResponse
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
async def get_current_user(request: Request, response:Response, db:AsyncSession=Depends(get_db)):

    access_token = request.cookies.get("accessToken")
    refresh_token = request.cookies.get("refreshToken")

    if not access_token:

        if not refresh_token:
            raise HTTPException(status_code=401, detail="Not authenticated")


        try:
            email = await auth_service.decode_token(refresh_token, expected_scope="refresh_token")

            new_access_token = auth_service.create_access_token({"sub": email})
            user = await repositories_users.get_user_by_email(email,db)

            response.set_cookie(
                key="accessToken",
                value=new_access_token,
                httponly=True,
                max_age=900,  # 15 минут
                path="/"
            )
            return user
        except HTTPException:
            raise HTTPException(status_code=401, detail="Invalid refresh token")


    try:
        email = await auth_service.decode_token(access_token, expected_scope="access_token")

        print(email)
        user = await repositories_users.get_user_by_email(email, db)

        return {"username":user.username,"email":user.email,"avatar":user.avatar}
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid access token")




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