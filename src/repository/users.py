from fastapi import Depends, Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar

from src.database.db import get_db
from src.database.models import User
from src.schemas import UserSchema
from src.services.auth import auth_service


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
    print(user_data)

    access_token = await auth_service.create_access_token({"sub": user.email})
    refresh_token = await auth_service.create_refresh_token({"sub": user.email})
    await update_token(user, refresh_token, db)

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        max_age=60 * 15,
        samesite="none",
        secure=False
    )
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        max_age=60 * 60 * 24 * 7,
        samesite="none",
        secure=False
    )

    return user_data