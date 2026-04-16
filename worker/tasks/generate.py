"""슬라이드 생성 Celery 태스크: 크롤링 → Gemini → DB 저장"""
import asyncio
import json
import logging
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

from sqlalchemy import update
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from backend.core.config import settings
from backend.models.generation import Generation
from shared.crawler import crawl
from shared.gemini_client import generate_slide_content
from worker.celery_app import app

logger = logging.getLogger(__name__)

_engine = create_async_engine(settings.database_url, echo=False)
_Session = async_sessionmaker(_engine, expire_on_commit=False)


async def _set_status(generation_id: str, status: str, **kwargs):
    """Generation 상태 업데이트"""
    async with _Session() as session:
        values = {"status": status, **kwargs}
        await session.execute(
            update(Generation)
            .where(Generation.id == generation_id)
            .values(**values)
        )
        await session.commit()


@app.task(bind=True, name="tasks.generate_slides")
def generate_slides(self, generation_id: str, url: str, language: str = "ko"):
    """URL → 크롤링 → Gemini → slide_json DB 저장"""
    asyncio.run(_generate_slides_async(generation_id, url, language))


async def _generate_slides_async(generation_id: str, url: str, language: str):
    try:
        # 1. 크롤링
        await _set_status(generation_id, "crawling")
        logger.info(f"[{generation_id}] 크롤링 시작: {url}")
        result = await crawl(url)

        if result.error:
            await _set_status(generation_id, "failed", error_message=f"크롤링 실패: {result.error}")
            return

        crawled_text = f"제목: {result.title}\n\n{result.text}"
        logger.info(f"[{generation_id}] 크롤링 완료: {len(crawled_text)}자")

        # 2. Gemini 구조화
        await _set_status(generation_id, "structuring")
        logger.info(f"[{generation_id}] Gemini 생성 시작")
        slide_content = generate_slide_content(
            crawled_text=crawled_text,
            url=url,
            language=language,
            api_key=settings.gemini_api_key,
        )

        # 3. DB 저장 (ready_to_edit)
        slide_json_str = slide_content.model_dump_json()
        await _set_status(
            generation_id,
            "ready_to_edit",
            slide_json=slide_json_str,
        )
        logger.info(f"[{generation_id}] 완료 — ready_to_edit")

    except Exception as e:
        logger.error(f"[{generation_id}] 태스크 실패: {e}")
        await _set_status(generation_id, "failed", error_message=str(e))
