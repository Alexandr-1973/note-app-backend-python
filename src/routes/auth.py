from fastapi import APIRouter, HTTPException, Depends, status, Response, Request
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.db import get_db
from src.repository import users as repositories_users
from src.repository.users import create_tokens_and_set_cookies
from src.schemas import UserSchema, UserResponse
from src.services.auth import auth_service

router = APIRouter(prefix='/auth', tags=['auth'])



@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(response: Response, body: UserSchema, db: AsyncSession = Depends(get_db)):
    exist_user = await repositories_users.get_user_by_email(body.email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")

    body.password = auth_service.get_password_hash(body.password)
    new_user = await repositories_users.create_user(body, db)

    return await create_tokens_and_set_cookies(new_user, response, db)


@router.post("/login", response_model=UserResponse)
async def login(response: Response, body: UserSchema, db: AsyncSession = Depends(get_db)):
    user = await repositories_users.get_user_by_email(body.email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="HTTP 401 Unauthorized")
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="HTTP 401 Unauthorized")

    return await create_tokens_and_set_cookies(user, response, db)


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    refresh_token = request.cookies.get("refreshToken")

    if refresh_token:
        try:
            email = await auth_service.decode_token(refresh_token, expected_scope="refresh_token")
            user = await repositories_users.get_user_by_email(email, db)
            if user:
                 await repositories_users.update_token(user, None, db)
        except Exception:
            pass

    response.delete_cookie(key="accessToken", path="/")
    response.delete_cookie(key="refreshToken", path="/")

    return {"message": "Successfully logged out"}


@router.get("/refresh_token")
async def refresh_token(request: Request, response: Response, db: AsyncSession = Depends(get_db)):
    token = request.cookies.get("refreshToken")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing refresh token")

    try:
        email = await auth_service.decode_token(token, expected_scope="refresh_token")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = await repositories_users.get_user_by_email(email, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    if user.refresh_token != token:
        await repositories_users.update_token(user, None, db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    access_token = await auth_service.create_access_token(data={"sub": email})
    new_refresh_token = await auth_service.create_refresh_token(data={"sub": email})

    await repositories_users.update_token(user, new_refresh_token, db)

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        path="/",
        samesite="none",
        secure=True
    )
    response.set_cookie(
        key="refreshToken",
        value=new_refresh_token,
        httponly=True,
        path="/",
        samesite="none",
        secure=True
    )

    return {"success": True}