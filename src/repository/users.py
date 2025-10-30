from fastapi import Depends, Response, Request, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from src.database.db import get_db
from src.database.models import User
from src.schemas import UserSchema
from src.services.auth import auth_service
from src.utils.cookies import set_auth_cookies


async def get_user_by_email(email: str, db: AsyncSession):
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalar_one_or_none()
    return user


async def create_user(body: UserSchema, db: AsyncSession = Depends(get_db)):
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image(default="identicon")
    except Exception as err:
        print(err)

    new_user = User(**body.model_dump(), avatar=avatar)
    new_user.username=new_user.email
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: User, token: str | None, db: AsyncSession):
    user.refresh_token = token
    await db.commit()

async def create_tokens_and_set_cookies(user: User, response: Response, db: AsyncSession):
    user_data={
        "username": user.username,
        "email": user.email,
        "avatar": user.avatar
    }

    access_token = await auth_service.create_access_token({"sub": user.email})
    refresh_token = await auth_service.create_refresh_token({"sub": user.email})
    await update_token(user, refresh_token, db)
    set_auth_cookies(response, access_token, refresh_token)

    return user_data


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)):
    access_token = request.cookies.get("accessToken")
    if not access_token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    try:
        email = await auth_service.decode_token(access_token, expected_scope="access_token")
        user = await get_user_by_email(email, db)

        return user

    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid or expired access token", headers={"X-Token-Expired": "1"},)