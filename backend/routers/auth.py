from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from backend.core.config import settings
from backend.core.database import get_db
from backend.core.security import create_access_token, create_refresh_token, decode_token
from backend.models.user import User
from backend.models.token import TokenBalance, TokenTransaction
from backend.schemas.auth import TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login():
    """Google OAuth 로그인 URL로 리다이렉트"""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/callback", response_model=TokenResponse)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Google 콜백: code → 유저 정보 → JWT 발급"""
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        })
        token_data = token_resp.json()

        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    result = await db.execute(select(User).where(User.email == userinfo["email"]))
    user = result.scalar_one_or_none()

    if user is None:
        user = User(
            email=userinfo["email"],
            name=userinfo.get("name", ""),
            picture=userinfo.get("picture"),
            is_admin=(userinfo["email"] == settings.admin_email),
        )
        db.add(user)
        await db.flush()

        balance = TokenBalance(user_id=user.id, balance=2)
        db.add(balance)

        tx = TokenTransaction(
            user_id=user.id,
            transaction_type="signup_bonus",
            amount=2,
            note="가입 보너스",
        )
        db.add(tx)
        await db.commit()
        await db.refresh(user)
    else:
        await db.commit()

    payload = {"sub": str(user.id), "email": user.email}
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


async def get_current_user(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> User:
    """JWT에서 현재 유저 추출 (Depends용)"""
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    authorization: str = "",
    db: AsyncSession = Depends(get_db),
):
    """현재 로그인 유저 정보"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ")[1]
    user = await get_current_user(token, db)
    return user
