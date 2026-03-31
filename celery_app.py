"""
celery_app.py — Celery + Redis 백그라운드 태스크 (슬라이드 파이프라인)
USE_CELERY=true 일 때만 사용됨
"""
import os
import json
import sqlite3
import logging

from celery import Celery

logger = logging.getLogger(__name__)

REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')

celery = Celery('webtoslide', broker=REDIS_URL, backend=REDIS_URL)
celery.conf.update(
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    task_track_started=True,
    task_time_limit=600,          # 10분 hard limit
    task_soft_time_limit=540,     # 9분 soft limit
    worker_concurrency=1,         # 동시 1개 파이프라인 (4GB 서버 메모리 제한)
    worker_prefetch_multiplier=1,
)

JOB_TTL = 7200  # 2시간

# ── Redis 클라이언트 (lazy init) ──────────────────────────────────────────
_redis = None

def _get_redis():
    global _redis
    if _redis is None:
        import redis
        _redis = redis.Redis.from_url(REDIS_URL, decode_responses=True)
    return _redis


# ── Standalone DB 헬퍼 (Flask context 없이 직접 SQLite 접근) ─────────────
def _get_db_path():
    base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, 'instance', 'tickdeck.db')


def _update_generation_status(gen_id, status):
    try:
        conn = sqlite3.connect(_get_db_path(), timeout=10)
        conn.execute(
            "UPDATE generations SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (status, gen_id)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"DB 업데이트 실패 (gen_id={gen_id}): {e}")


def _refund_and_fail(user_id, gen_id):
    try:
        conn = sqlite3.connect(_get_db_path(), timeout=10)
        conn.execute("UPDATE users SET tokens = tokens + 1 WHERE id = ?", (user_id,))
        conn.execute(
            "INSERT INTO token_history (user_id, amount, reason, generation_id) VALUES (?, 1, 'refund_failed', ?)",
            (user_id, gen_id)
        )
        conn.execute(
            "UPDATE generations SET status = 'failed', completed_at = CURRENT_TIMESTAMP WHERE id = ?",
            (gen_id,)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"환불 실패 (user_id={user_id}, gen_id={gen_id}): {e}")


# ── Celery 태스크 ─────────────────────────────────────────────────────────
@celery.task(bind=True, name='webtoslide.run_pipeline',
             soft_time_limit=540, time_limit=600)
def run_pipeline_task(self, job_id, url, company, narrative_type, mood, purpose,
                      brand_color, user_id, gen_id, slide_lang='ko'):
    """run_pipeline()을 Celery 워커에서 실행, 진행 상황을 Redis에 기록"""
    import re as _re
    from celery.exceptions import SoftTimeLimitExceeded
    from web_to_slide.pipeline import run_pipeline
    logger.info(f"[Celery] slide_lang={slide_lang}, user_id={user_id}, gen_id={gen_id}")

    r = _get_redis()

    # 초기 상태
    r.set(f'job:{job_id}:status', 'running')
    r.set(f'job:{job_id}:meta', json.dumps({'user_id': user_id, 'gen_id': gen_id}))

    def on_progress(line):
        if line.strip():
            r.rpush(f'job:{job_id}:lines', line)
            # 실시간 SSE용 pub/sub
            r.publish(f'job:{job_id}:channel', json.dumps({'line': line}))

    from web_to_slide.config import clear_slide_cache

    if gen_id:
        _update_generation_status(gen_id, 'processing')

    try:
        result = run_pipeline(url, company or None, progress_fn=on_progress,
                              narrative_type=narrative_type, mood=mood,
                              purpose=purpose, brand_color=brand_color, slide_lang=slide_lang)
        r.set(f'job:{job_id}:result', json.dumps(result, ensure_ascii=False))
        r.set(f'job:{job_id}:status', 'done')
        r.publish(f'job:{job_id}:channel', json.dumps({'status': 'done'}))
        if gen_id:
            _update_generation_status(gen_id, 'completed')
    except SoftTimeLimitExceeded:
        # M7: 타임아웃 시 깔끔한 정리
        logger.error(f"[Celery] 타임아웃 (9분 초과): job={job_id}")
        on_progress("  ⚠ 생성 시간 초과 (9분) — 자동 종료")
        r.set(f'job:{job_id}:status', 'error')
        r.set(f'job:{job_id}:error', '생성 시간이 초과되었습니다. 다시 시도해 주세요.')
        r.publish(f'job:{job_id}:channel', json.dumps({'status': 'error', 'error': '생성 시간 초과'}))
        if user_id and gen_id:
            _refund_and_fail(user_id, gen_id)
            on_progress("  → 토큰 환불 완료")
        return
    except Exception as e:
        import traceback as _tb
        logger.error(f"파이프라인 오류:\n{_tb.format_exc()}")  # 서버 로그에만
        on_progress(f"  ⚠ 오류 발생: 잠시 후 재시도합니다")

        # 캐시 삭제 후 재시도
        _slug = company or url.split('//')[-1].split('/')[0].replace('.', '')
        clear_slide_cache(_slug, on_progress)
        on_progress("  → 캐시 삭제 후 재시도 중...")

        try:
            result = run_pipeline(url, company or None, progress_fn=on_progress,
                                  narrative_type=narrative_type, mood=mood,
                                  purpose=purpose, brand_color=brand_color, slide_lang=slide_lang)
            r.set(f'job:{job_id}:result', json.dumps(result, ensure_ascii=False))
            r.set(f'job:{job_id}:status', 'done')
            r.publish(f'job:{job_id}:channel', json.dumps({'status': 'done'}))
            if gen_id:
                _update_generation_status(gen_id, 'completed')
        except Exception as e2:
            logger.error(f"최종 실패: {_tb.format_exc()}")
            r.set(f'job:{job_id}:status', 'error')
            r.set(f'job:{job_id}:error', str(e2))
            r.publish(f'job:{job_id}:channel', json.dumps({'status': 'error', 'error': str(e2)}))
            if user_id and gen_id:
                _refund_and_fail(user_id, gen_id)
                on_progress("  → 토큰 환불 완료")
    finally:
        # 모든 키에 TTL 설정
        for suffix in ['status', 'lines', 'result', 'error', 'meta']:
            r.expire(f'job:{job_id}:{suffix}', JOB_TTL)
