from fastapi import Response

def set_auth_cookies(response: Response, access_token: str, refresh_token: str):

    response.set_cookie(
        key="accessToken",
        value=access_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 15,
    )
    response.set_cookie(
        key="refreshToken",
        value=refresh_token,
        httponly=True,
        samesite="lax",
        secure=False,
        path="/",
        max_age=60 * 60 * 24 * 7,
    )