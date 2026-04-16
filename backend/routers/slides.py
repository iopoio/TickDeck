from fastapi import APIRouter

router = APIRouter(prefix="/api/slides", tags=["slides"])


@router.post("/generate")
async def generate_slide():
    """슬라이드 생성 요청 (Phase 3에서 구현)"""
    return {"message": "coming soon"}
