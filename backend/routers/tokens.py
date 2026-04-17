from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.core.database import get_db
from backend.routers.auth import get_current_user
from backend.models.token import TokenBalance

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("/balance")
async def get_balance(
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
):
    """토큰 잔액 조회: DB에서 실제 잔액 확인"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization required")
    token = authorization.split(" ")[1]
    
    user = await get_current_user(token, db)
    
    result = await db.execute(
        select(TokenBalance).where(TokenBalance.user_id == user.id)
    )
    balance_obj = result.scalar_one_or_none()
    
    return {"balance": balance_obj.balance if balance_obj else 0}
