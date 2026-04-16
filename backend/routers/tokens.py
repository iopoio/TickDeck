from fastapi import APIRouter

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("/balance")
async def get_balance():
    """토큰 잔액 조회 (Phase 3에서 구현)"""
    return {"balance": 0}
