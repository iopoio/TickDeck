from fastapi import APIRouter

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/")
async def list_history():
    """생성 이력 (Phase 4에서 구현)"""
    return {"items": []}
