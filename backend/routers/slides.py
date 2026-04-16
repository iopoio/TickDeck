"""슬라이드 생성/상태/확정/다운로드 라우터"""
import json
import uuid
import logging
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.core.database import get_db
from backend.core.security import decode_token
from backend.models.generation import Generation
from backend.models.token import TokenBalance, TokenTransaction
from backend.models.user import User
from backend.schemas.auth import UserResponse
from shared.schemas import GenerationRequest, GenerationStatus, SlideContent
from shared.pptx_builder import build_pptx

router = APIRouter(prefix="/api/slides", tags=["slides"])
logger = logging.getLogger(__name__)

PPTX_DIR = Path("tmp/pptx")
PPTX_DIR.mkdir(parents=True, exist_ok=True)


async def _get_current_user(authorization: str, db: AsyncSession) -> User:
    """Authorization 헤더에서 유저 추출"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ")[1]
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/generate")
async def generate_slide(
    req: GenerationRequest,
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
):
    """URL → 슬라이드 생성 요청. 토큰 1개 Lock."""
    user = await _get_current_user(authorization, db)

    # 토큰 잔액 확인
    result = await db.execute(select(TokenBalance).where(TokenBalance.user_id == user.id))
    balance = result.scalar_one_or_none()
    if not balance or balance.balance < 1:
        raise HTTPException(status_code=402, detail="토큰이 부족합니다")

    # 토큰 Lock (잔액 차감 + 트랜잭션 기록)
    balance.balance -= 1
    lock_tx = TokenTransaction(
        user_id=user.id,
        transaction_type="generation_lock",
        amount=-1,
        note=f"생성 Lock: {req.url[:100]}",
    )
    db.add(lock_tx)

    # Generation 레코드 생성
    generation_id = str(uuid.uuid4())
    generation = Generation(
        id=generation_id,
        user_id=user.id,
        url=req.url,
        language=req.language,
        status="pending",
    )
    db.add(generation)
    await db.commit()

    # Celery 태스크 큐잉
    try:
        from worker.tasks.generate import generate_slides
        generate_slides.delay(generation_id, req.url, req.language)
    except Exception as e:
        logger.error(f"Celery 태스크 큐잉 실패: {e}")
        # 태스크 실패 시 토큰 환불
        balance.balance += 1
        refund_tx = TokenTransaction(
            user_id=user.id,
            transaction_type="generation_refund",
            amount=1,
            note="태스크 큐잉 실패 환불",
        )
        db.add(refund_tx)
        await db.commit()
        raise HTTPException(status_code=500, detail="생성 요청 실패")

    return {"generation_id": generation_id, "status": "pending"}


@router.get("/{generation_id}/status")
async def get_status(
    generation_id: str,
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
):
    """생성 상태 폴링"""
    user = await _get_current_user(authorization, db)

    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == user.id,  # IDOR 방지
        )
    )
    generation = result.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="생성 기록을 찾을 수 없습니다")

    slide_content = None
    if generation.slide_json and generation.status == "ready_to_edit":
        try:
            slide_content = SlideContent.model_validate_json(generation.slide_json)
        except Exception as e:
            logger.error(f"slide_json 파싱 실패: {e}")

    return GenerationStatus(
        generation_id=generation_id,
        status=generation.status,
        slide_content=slide_content,
        error_message=generation.error_message,
        pptx_url=f"/api/slides/{generation_id}/download" if generation.pptx_path else None,
    )


@router.post("/{generation_id}/confirm")
async def confirm_generation(
    generation_id: str,
    slide_content: SlideContent,
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
):
    """편집된 슬라이드 확정 → PPTX 빌드"""
    user = await _get_current_user(authorization, db)

    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == user.id,
        )
    )
    generation = result.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="생성 기록을 찾을 수 없습니다")
    if generation.status not in ("ready_to_edit", "failed"):
        raise HTTPException(status_code=400, detail=f"현재 상태에서 확정 불가: {generation.status}")

    # PPTX 빌드
    generation.status = "building_pptx"
    await db.commit()

    try:
        pptx_bytes = build_pptx(slide_content.model_dump())
        pptx_path = PPTX_DIR / f"{generation_id}.pptx"
        pptx_path.write_bytes(pptx_bytes)

        generation.status = "done"
        generation.pptx_path = str(pptx_path)
        generation.slide_json = slide_content.model_dump_json()

        # 토큰 Confirm 기록
        confirm_tx = TokenTransaction(
            user_id=user.id,
            transaction_type="generation_confirm",
            amount=0,
            note=f"생성 확정: {generation_id}",
        )
        db.add(confirm_tx)
        await db.commit()

    except Exception as e:
        generation.status = "failed"
        generation.error_message = str(e)
        # 토큰 환불
        balance_result = await db.execute(select(TokenBalance).where(TokenBalance.user_id == user.id))
        balance = balance_result.scalar_one_or_none()
        if balance:
            balance.balance += 1
            refund_tx = TokenTransaction(
                user_id=user.id,
                transaction_type="generation_refund",
                amount=1,
                note="PPTX 빌드 실패 환불",
            )
            db.add(refund_tx)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"PPTX 생성 실패: {e}")

    return {"status": "done", "pptx_url": f"/api/slides/{generation_id}/download"}


@router.get("/{generation_id}/download")
async def download_pptx(
    generation_id: str,
    authorization: str = Header(""),
    db: AsyncSession = Depends(get_db),
):
    """생성된 PPTX 다운로드"""
    user = await _get_current_user(authorization, db)

    result = await db.execute(
        select(Generation).where(
            Generation.id == generation_id,
            Generation.user_id == user.id,
        )
    )
    generation = result.scalar_one_or_none()
    if not generation:
        raise HTTPException(status_code=404, detail="생성 기록을 찾을 수 없습니다")
    if not generation.pptx_path:
        raise HTTPException(status_code=404, detail="PPTX 파일이 없습니다")

    pptx_path = Path(generation.pptx_path)
    if not pptx_path.exists():
        raise HTTPException(status_code=404, detail="PPTX 파일이 삭제됐습니다")

    return FileResponse(
        path=str(pptx_path),
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        filename=f"tickdeck_{generation_id[:8]}.pptx",
    )
