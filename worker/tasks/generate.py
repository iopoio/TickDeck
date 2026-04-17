"""슬라이드 생성 Celery 태스크: 크롤링 → Gemini → Quality → DB 저장 (동기 방식)"""
import asyncio
import json
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'shared'))

import psycopg2
from backend.core.config import settings
from shared.crawler import crawl
from shared.gemini_client import generate_slide_content
from shared.quality import validate_and_fix
from worker.celery_app import app

logger = logging.getLogger(__name__)

# asyncpg URL → psycopg2 DSN 변환
def _get_dsn() -> str:
    url = settings.database_url
    # postgresql+asyncpg://user:pass@host:port/db → postgresql://user:pass@host:port/db
    return url.replace("postgresql+asyncpg://", "postgresql://")


def _set_status(generation_id: str, status: str, **kwargs):
    """Generation 상태 동기 업데이트 (psycopg2)"""
    dsn = _get_dsn()
    fields = {"status": status, "updated_at": datetime.utcnow(), **kwargs}
    set_clause = ", ".join(f"{k} = %s" for k in fields)
    values = list(fields.values()) + [generation_id]

    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            cur.execute(
                f"UPDATE generations SET {set_clause} WHERE id = %s",
                values
            )
        conn.commit()
    finally:
        conn.close()


class PermanentError(Exception):
    """재시도 불가능한 오류: 크롤링 거부, 쿼터 초과 등"""
    pass

class TransientError(Exception):
    """재시도 가능한 오류: 일시적 네트워크 장애, 타임아웃 등"""
    pass


def _refund_token(generation_id: str):
    """태스크 실패 시 해당 generation에 묶인 토큰을 자동 환불"""
    dsn = _get_dsn()
    conn = psycopg2.connect(dsn)
    try:
        with conn.cursor() as cur:
            # user_id와 lock_tx_id 조회
            cur.execute("SELECT user_id, lock_tx_id FROM generations WHERE id = %s", (generation_id,))
            row = cur.fetchone()
            if not row or row[1] is None:
                logger.info(f"[{generation_id}] 환불 대상 아님 (이미 환불됨 or 트랜잭션 없음)")
                return
                
            user_id, lock_tx_id = row
            
            # 1. TokenTransaction 생성 (refund)
            cur.execute(
                "INSERT INTO token_transactions (user_id, transaction_type, amount, note, created_at) "
                "VALUES (%s, 'generation_refund', 1, %s, NOW())",
                (user_id, f"자동 환불: {generation_id}")
            )
            
            # 2. TokenBalance 복구
            cur.execute("UPDATE token_balances SET balance = balance + 1, updated_at = NOW() WHERE user_id = %s", (user_id,))
            
            # 3. Generation에서 lock_tx_id 제거 (중복 환불 방지)
            cur.execute("UPDATE generations SET lock_tx_id = NULL WHERE id = %s", (generation_id,))
            
        conn.commit()
        logger.info(f"[{generation_id}] 토큰 환불 완료")
    except Exception as e:
        logger.error(f"[{generation_id}] 토큰 환불 중 치명적 오류: {e}")
    finally:
        conn.close()


@app.task(bind=True, name="tasks.generate_slides", autoretry_for=(TransientError,), retry_kwargs={'max_retries': 3, 'countdown': 5})
def generate_slides(self, generation_id: str, url: str, language: str = "ko"):
    """URL → 크롤링 → Gemini(3단계) → Quality Check → DB 저장"""
    try:
        # 1. 크롤링 (async → sync 실행)
        _set_status(generation_id, "crawling")
        logger.info(f"[{generation_id}] 크롤링 시작: {url}")

        loop = asyncio.new_event_loop()
        try:
            result = loop.run_until_complete(crawl(url))
        except Exception as e:
            # 네트워크 오류 등은 TransientError로 간주하여 재시도
            raise TransientError(f"크롤링 오류 (재시도 예상): {e}")
        finally:
            loop.close()

        if result.error:
            # 403, 404 등 명확한 에러는 PermanentError로 즉시 실패 처리
            err_msg = str(result.error)
            if "403" in err_msg or "404" in err_msg or "Block" in err_msg:
                raise PermanentError(f"크롤링 거부/불가: {err_msg}")
            else:
                raise TransientError(f"일시적 크롤링 실패: {err_msg}")

        crawled_text = f"제목: {result.title}\n\n{result.text}"
        
        # 2. Gemini 구조화 (3단계 파이프라인)
        _set_status(generation_id, "structuring")
        logger.info(f"[{generation_id}] Gemini 3단계 에이전트 시작")
        
        try:
            slide_content = generate_slide_content(
                crawled_text=crawled_text,
                url=url,
                language=language,
                api_key=settings.gemini_api_key,
            )
        except Exception as e:
            err_msg = str(e)
            if "quota" in err_msg.lower() or "limit" in err_msg.lower():
                raise PermanentError(f"Gemini 할당량 초과: {err_msg}")
            else:
                raise TransientError(f"Gemini 일시적 오류: {err_msg}")

        # 3. Quality Check 및 자동 수정
        slide_dict = slide_content.model_dump()
        fixed_slide_dict = validate_and_fix(slide_dict)

        # 4. DB 저장 (ready_to_edit)
        import json as _json
        def _clean(obj):
            if isinstance(obj, str):
                return obj.encode('utf-8', errors='ignore').decode('utf-8')
            if isinstance(obj, list):
                return [_clean(i) for i in obj]
            if isinstance(obj, dict):
                return {k: _clean(v) for k, v in obj.items()}
            return obj
            
        slide_json_str = _json.dumps(_clean(fixed_slide_dict), ensure_ascii=False)
        _set_status(generation_id, "ready_to_edit", slide_json=slide_json_str)
        logger.info(f"[{generation_id}] 완료 — ready_to_edit")

    except PermanentError as e:
        logger.error(f"[{generation_id}] 영구 오류 (환불 진행): {e}")
        _refund_token(generation_id)
        _set_status(generation_id, "failed", error_message=str(e))
    except TransientError as e:
        # autoretry_for에 의해 자동으로 재시도됨
        # 만약 마지막 재시도에서도 실패하면 Celery가 기본적으로 raise함
        # 아래 Exception에서 최종 환불 처리
        logger.warning(f"[{generation_id}] 일시적 오류 (재시도 예약): {e}")
        raise e
    except Exception as e:
        # 예상치 못한 일반 오류
        logger.error(f"[{generation_id}] 예외 발생: {e}")
        # 재시도 횟수를 모두 소진했거나 일반 오류인 경우 환불
        if self.request.retries >= self.max_retries:
            logger.info(f"[{generation_id}] 재시도 횟수 초과로 인한 환불")
            _refund_token(generation_id)
            _set_status(generation_id, "failed", error_message=f"최종 실패: {str(e)}")
        else:
            # 예상치 못한 시스템 오류 등도 재시도는 해봄
            raise self.retry(exc=e)
