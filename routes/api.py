import json
import os
import io
import uuid
import threading
import time
import tempfile
import subprocess
from pathlib import Path
from flask import Blueprint, request, jsonify, session, Response, send_file, current_app

from web_to_slide.database import get_db, add_tokens, get_user_by_id, check_and_deduct_token, create_generation, complete_generation, refund_token
from web_to_slide.pipeline import run_pipeline
from routes import login_required
from extensions import limiter, _log, redis_client, JOBS, USE_CELERY

api_bp = Blueprint('api', __name__)
BASE_DIR = Path(__file__).parent.parent

@api_bp.route("/api/token/free-charge", methods=["POST"])
@limiter.limit("2 per day")
@login_required
def free_charge():
    """무료 토큰 2개 충전 (1일 2회 제한)"""
    user_id = session['user_id']
    # 오늘 이미 충전했는지 DB 체크
    db = get_db()
    today_count = db.execute(
        "SELECT COUNT(*) c FROM token_history WHERE user_id = ? AND reason = 'free_charge' AND DATE(created_at) = DATE('now')",
        (user_id,)
    ).fetchone()['c']
    if today_count >= 2:
        return jsonify({"ok": False, "error": "오늘 충전 횟수를 초과했습니다."}), 429
    add_tokens(user_id, 2, 'free_charge')
    user = get_user_by_id(user_id)
    return jsonify({"ok": True, "tokens": user['tokens']})


@api_bp.route("/api/survey/check")
@login_required
def survey_check():
    """설문 참여 여부 확인"""
    user_id = session['user_id']
    db = get_db()
    done = db.execute("SELECT id FROM surveys WHERE user_id = ?", (user_id,)).fetchone()
    return jsonify({"done": bool(done)})


@api_bp.route("/api/survey", methods=["POST"])
@login_required
def submit_survey():
    """설문 제출 → 토큰 2개 지급 (계정당 1회)"""
    user_id = session['user_id']
    db = get_db()

    # 중복 방지
    existing = db.execute("SELECT id FROM surveys WHERE user_id = ?", (user_id,)).fetchone()
    if existing:
        return jsonify({"error": "이미 설문에 참여하셨습니다."}), 400

    data = request.get_json(force=True)
    db.execute("""
        INSERT INTO surveys
        (user_id, q1_industry, q2_role, q3_company_size,
         q4_frequency, q5_current_method, q6_payment_type,
         q7_price, q8_features, q9_feedback)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        data.get('q1'), data.get('q2'), data.get('q3'),
        data.get('q4'), json.dumps(data.get('q5', [])),
        data.get('q6'), data.get('q7'),
        json.dumps(data.get('q8', [])),
        data.get('q9')
    ))

    # 토큰 지급
    db.execute("UPDATE users SET tokens = tokens + 2 WHERE id = ?", (user_id,))
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason) VALUES (?, 2, 'survey')",
        (user_id,)
    )
    db.commit()

    user = get_user_by_id(user_id)
    return jsonify({"ok": True, "tokens": user['tokens']})


@api_bp.route("/api/regen-slide", methods=["POST"])
@login_required
def api_regen_slide():
    """단일 슬라이드 AI 재생성 — 토큰 소모 없음 (텍스트만 재작성)"""
    data = request.get_json(force=True)
    slide_type = data.get('slide_type', '')
    headline = data.get('headline', '')
    company_name = data.get('company_name', '')
    factbook_url = data.get('factbook_url', '')

    if not slide_type:
        return jsonify({"ok": False, "error": "slide_type 필수"}), 400

    try:
        from web_to_slide.agents import _call_gemini_with_retry
        prompt = f"""회사명: {company_name}
슬라이드 타입: {slide_type}
기존 헤드라인: {headline}
참고 URL: {factbook_url}

이 슬라이드의 카피를 다시 작성해주세요.
규칙:
- headline: 핵심 메시지 (10~25자, 한국어)
- subheadline: 보조 설명 (15~30자, 선택)
- body: 2~4개 bullet 항목 (각 15자 이상, "짧은제목: 설명" 형식)
- 마크다운 금지, 문장형(~다/~요) 금지
- 데이터에 없는 내용을 지어내지 말 것
- JSON만 출력: {{"headline":"...","subheadline":"...","body":["...","..."]}}"""

        resp = _call_gemini_with_retry(
            model="models/gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.3, "max_output_tokens": 2000}
        )
        import re
        text = resp.text.strip()
        text = re.sub(r'```json\s*', '', text)
        text = re.sub(r'```', '', text)
        start = text.find('{')
        end = text.rfind('}')
        if start != -1 and end != -1:
            slide = json.loads(text[start:end+1])
            return jsonify({"ok": True, "slide": slide})
        return jsonify({"ok": False, "error": "JSON 파싱 실패"}), 500
    except Exception as e:
        _log(f"[regen-slide] 오류: {e}")
        return jsonify({"ok": False, "error": "AI 재생성 중 오류가 발생했습니다."}), 500


@api_bp.route("/api/generations")
@login_required
def api_generations():
    """내 생성 이력 목록"""
    user_id = session['user_id']
    db = get_db()
    rows = db.execute(
        "SELECT id, url, company_name, purpose, status, created_at, completed_at "
        "FROM generations WHERE user_id = ? ORDER BY created_at DESC LIMIT 20",
        (user_id,)
    ).fetchall()
    # 직전 PDF 존재 여부 확인 (파일명이 다양할 수 있으므로 *.pdf로 체크)
    import glob as _glob
    pdf_dir = os.path.join(BASE_DIR, 'user_pdfs', str(user_id))
    has_pdf = bool(_glob.glob(os.path.join(pdf_dir, '*.pdf')))
    return jsonify({
        "ok": True,
        "generations": [dict(r) for r in rows],
        "has_latest_pdf": has_pdf,
    })


@api_bp.route("/api/generations/latest-pdf")
@login_required
def download_latest_pdf():
    """직전 생성 PDF 다운로드"""
    import glob
    user_id = session['user_id']
    user_pdf_dir = os.path.join(BASE_DIR, 'user_pdfs', str(user_id))
    pdfs = glob.glob(os.path.join(user_pdf_dir, '*.pdf'))
    if not pdfs:
        return jsonify({"error": "저장된 PDF가 없습니다"}), 404
    pdf_path = pdfs[0]
    return send_file(pdf_path, mimetype='application/pdf',
                     as_attachment=True, download_name=os.path.basename(pdf_path))


# ── 파이프라인 실행 ─────────────────────────────────────────────────────────
def _run(app_context, job_id: str, url: str, company: str,
         narrative_type: str = "auto", mood: str = "professional", purpose: str = "brand",
         brand_color: str = "", slide_lang: str = "ko"):
    job = JOBS[job_id]

    def on_progress(line: str):
        if line.strip():
            job["lines"].append(line)
            _log(line)

    import os, re as _re
    from web_to_slide.config import clear_slide_cache

    gen_id = job.get("gen_id")
    user_id = job.get("user_id")

    try:
        if gen_id:
            with app_context:
                complete_generation(gen_id, 'processing')
        result = run_pipeline(url, company or None, progress_fn=on_progress,
                              narrative_type=narrative_type, mood=mood, purpose=purpose,
                              brand_color=brand_color, slide_lang=slide_lang)
        job["result"] = result
        job["status"] = "done"
        if gen_id:
            with app_context:
                complete_generation(gen_id, 'completed')
    except Exception as e:
        import traceback as _tb
        err_str = str(e)
        _log("=== TRACEBACK ===\n" + _tb.format_exc() + "=================")  # 서버 로그에만
        on_progress(f"  ⚠ 오류 발생: 잠시 후 재시도합니다")
        _slug = company or url.split('//')[-1].split('/')[0].replace('.', '')
        clear_slide_cache(_slug, on_progress)
        on_progress("  → 캐시 삭제 후 재시도 중...")
        try:
            result = run_pipeline(url, company or None, progress_fn=on_progress,
                                  narrative_type=narrative_type, mood=mood, purpose=purpose,
                                  brand_color=brand_color)
            job["result"] = result
            job["status"] = "done"
            if gen_id:
                with app_context:
                    complete_generation(gen_id, 'completed')
        except Exception as e2:
            import traceback as _tb2
            _log("=== TRACEBACK2 ===\n" + _tb2.format_exc() + "=================")
            job["status"] = "error"
            job["error"] = str(e2)
            # 실패 시 토큰 환불
            if user_id and gen_id:
                with app_context:
                    refund_token(user_id, gen_id)
                    complete_generation(gen_id, 'failed')
                on_progress("  → 토큰 환불 완료")


@api_bp.route("/generate", methods=["POST"])
@limiter.limit("30 per hour")
@login_required
def generate():
    user_id = session['user_id']
    data    = request.get_json(force=True)
    url            = (data.get("url") or "").strip()
    company        = (data.get("company") or "").strip()
    narrative_type = (data.get("narrative_type") or "auto").strip()
    mood           = (data.get("mood") or "professional").strip()
    purpose        = (data.get("purpose") or "auto").strip()
    brand_color    = (data.get("brand_color") or "").strip()
    slide_lang     = (data.get("slide_lang") or "ko").strip()

    if not url:
        return jsonify({"error": "URL을 입력하세요."}), 400

    if not url.startswith("http"):
        url = "https://" + url

    # S3: SSRF 방지 — 내부 네트워크 접근 차단
    try:
        from urllib.parse import urlparse
        _parsed = urlparse(url)
        _host = (_parsed.hostname or '').lower()
        _blocked = ('localhost', '127.0.0.1', '0.0.0.0', '[::1]', 'metadata.google.internal')
        if (_host in _blocked
            or _host.startswith('10.') or _host.startswith('192.168.') or _host.startswith('172.')
            or _host.startswith('169.254.')  # 링크-로컬 (AWS 메타데이터 등)
            or _host.startswith('224.')      # 멀티캐스트
            or _host.startswith('240.')      # 예약 주소
        ):
            return jsonify({"error": "내부 네트워크 URL은 사용할 수 없습니다."}), 400
        if not _parsed.scheme in ('http', 'https'):
            return jsonify({"error": "http/https URL만 지원합니다."}), 400
    except Exception:
        return jsonify({"error": "올바른 URL 형식이 아닙니다."}), 400

    # 토큰 차감 (먼저 차감 → 실패 시 환불)
    remaining = check_and_deduct_token(user_id)
    if remaining is None:
        return jsonify({"error": "토큰이 부족합니다. 토큰을 충전해 주세요."}), 403

    # generation 기록
    gen_id = create_generation(user_id, url, company or None, purpose)

    # token_history 기록
    db = get_db()
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason, generation_id) VALUES (?, -1, 'generate', ?)",
        (user_id, gen_id)
    )
    db.commit()

    job_id = str(uuid.uuid4())

    # job_id를 DB에 저장 (새로고침 시 복원용)
    try:
        db.execute("UPDATE generations SET job_id = ? WHERE id = ?", (job_id, gen_id))
        db.commit()
    except Exception:
        pass  # job_id 컬럼 없는 구버전 DB에서도 동작

    if USE_CELERY:
        # Celery + Redis 모드
        from celery_app import run_pipeline_task
        run_pipeline_task.delay(
            job_id, url, company, narrative_type, mood, purpose, brand_color,
            user_id, gen_id, slide_lang
        )
    else:
        # In-Memory 모드 (로컬 개발)
        JOBS[job_id] = {"status": "running", "lines": [], "result": None, "error": None,
                        "user_id": user_id, "gen_id": gen_id}
        app_context = current_app.app_context()
        t = threading.Thread(target=_run, args=(app_context, job_id, url, company, narrative_type, mood, purpose, brand_color, slide_lang), daemon=True)
        t.start()

    return jsonify({"job_id": job_id, "remaining_tokens": remaining})


@api_bp.route("/stream/<job_id>")
def stream(job_id: str):
    """Server-Sent Events — 실시간 로그 + 완료 이벤트"""
    if USE_CELERY:
        return _stream_redis(job_id)
    return _stream_memory(job_id)


def _stream_memory(job_id):
    """In-Memory 모드 SSE"""
    def generate():
        sent = 0
        while True:
            job = JOBS.get(job_id)
            if not job:
                yield f"data: {json.dumps({'error': '존재하지 않는 작업입니다.'})}\n\n"
                break
            while sent < len(job["lines"]):
                yield f"data: {json.dumps({'line': job['lines'][sent]})}\n\n"
                sent += 1
            if job["status"] == "done":
                meta = job["result"].get("meta", {}) if job["result"] else {}
                slide_count = len(job["result"].get("slides", [])) if job["result"] else 0
                yield f"data: {json.dumps({'status': 'done', 'meta': meta, 'slide_count': slide_count})}\n\n"
                break
            elif job["status"] == "error":
                yield f"data: {json.dumps({'status': 'error', 'error': job.get('error', '')})}\n\n"
                break
            time.sleep(0.4)
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


def _stream_redis(job_id):
    """Celery + Redis 모드 SSE (pub/sub + LRANGE 하이브리드)"""
    def generate():
        r = redis_client
        pubsub = r.pubsub()
        pubsub.subscribe(f'job:{job_id}:channel')
        sent = 0
        try:
            while True:
                # 미전송 라인 catch-up
                lines = r.lrange(f'job:{job_id}:lines', sent, -1)
                for line in lines:
                    yield f"data: {json.dumps({'line': line})}\n\n"
                    sent += 1
                # 상태 확인
                status = r.get(f'job:{job_id}:status')
                if status == 'done':
                    result_raw = r.get(f'job:{job_id}:result')
                    result = json.loads(result_raw) if result_raw else {}
                    meta = result.get('meta', {})
                    slide_count = len(result.get('slides', []))
                    yield f"data: {json.dumps({'status': 'done', 'meta': meta, 'slide_count': slide_count})}\n\n"
                    break
                elif status == 'error':
                    error = r.get(f'job:{job_id}:error') or ''
                    yield f"data: {json.dumps({'status': 'error', 'error': error})}\n\n"
                    break
                elif status is None:
                    yield f"data: {json.dumps({'error': '존재하지 않는 작업입니다.'})}\n\n"
                    break
                # pub/sub 대기 (0.5초 타임아웃)
                pubsub.get_message(timeout=0.5)
        finally:
            pubsub.unsubscribe()
            pubsub.close()
    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@api_bp.route("/clear-cache", methods=["POST"])
def clear_cache():
    """URL에 해당하는 캐시 JSON 파일 삭제"""
    data = request.get_json(force=True) or {}
    url = (data.get("url") or "").strip()
    company = (data.get("company") or "").strip()

    # company 이름이 없으면 URL에서 추출
    if not company and url:
        host = url.split("//")[-1].split("/")[0].replace("www.", "")
        company = host.split(".")[0]

    if not company:
        return jsonify({"ok": False, "msg": "URL 또는 company 이름이 필요합니다."}), 400

    deleted = []
    for suffix in ["_text.json", "_img.json", ".json"]:
        cf = BASE_DIR / f"slide_{company}{suffix}"
        if cf.exists():
            cf.unlink()
            deleted.append(cf.name)
    if deleted:
        return jsonify({"ok": True, "files": deleted})
    return jsonify({"ok": False, "msg": f"캐시 없음: slide_{company}_*.json"})


@api_bp.route("/result/<job_id>")
def result(job_id: str):
    """완료된 작업의 JSON 결과 반환 (슬라이드 데이터 전체)"""
    if USE_CELERY:
        r = redis_client
        status = r.get(f'job:{job_id}:status')
        if status is None:
            return jsonify({"error": "존재하지 않는 작업입니다."}), 404
        if status != 'done':
            return jsonify({"error": "작업이 아직 완료되지 않았습니다.", "status": status}), 202
        result_raw = r.get(f'job:{job_id}:result')
        return Response(result_raw, mimetype='application/json')
    else:
        job = JOBS.get(job_id)
        if not job:
            return jsonify({"error": "존재하지 않는 작업입니다."}), 404
        if job["status"] != "done":
            return jsonify({"error": "작업이 아직 완료되지 않았습니다.", "status": job["status"]}), 202
        return jsonify(job["result"])


def _cleanup_stale_processing():
    """10분 이상 processing 상태인 작업 → failed 전환 + 토큰 환불"""
    try:
        db = get_db()
        stale = db.execute(
            "SELECT id, user_id FROM generations WHERE status = 'processing' AND created_at < datetime('now', '-10 minutes')"
        ).fetchall()
        for row in stale:
            db.execute("UPDATE generations SET status = 'failed', completed_at = CURRENT_TIMESTAMP WHERE id = ?", (row['id'],))
            db.execute("UPDATE users SET tokens = tokens + 1 WHERE id = ?", (row['user_id'],))
            db.execute(
                "INSERT INTO token_history (user_id, amount, reason, generation_id) VALUES (?, 1, 'refund_timeout', ?)",
                (row['user_id'], row['id'])
            )
        if stale:
            db.commit()
    except Exception:
        pass


@api_bp.route("/api/preview-cover", methods=["POST"])
def preview_cover():
    """
    Phase 1: 서버사이드 커버 생성 미리보기 API (토큰 소모 없음)
    """
    data = request.get_json(force=True) or {}
    brand = data.get('brand', {})
    headline = data.get('headline', '')
    sub = data.get('sub', '')
    logo_b64 = data.get('logo_b64')

    try:
        from web_to_slide.pptx_builder import build_cover
        pptx_bytes = build_cover(brand, headline, sub, logo_b64)
        return send_file(
            io.BytesIO(pptx_bytes),
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name='cover_preview.pptx'
        )
    except Exception as e:
        _log(f"[preview-cover] Error: {e}")
        return jsonify({"error": "커버 생성 중 오류가 발생했습니다."}), 500


@api_bp.route("/api/merge-cover", methods=["POST"])
def merge_cover_api():
    """Phase 1.5: PptxGenJS PPTX의 커버를 python-pptx 커버로 교체 (로컬 테스트용)"""
    try:
        pptx_file = request.files.get('file')
        brand_json = request.form.get('brand', '{}')
        headline = request.form.get('headline', '')
        sub = request.form.get('sub', '')
        logo_b64 = request.form.get('logo_b64')

        if not pptx_file:
            return jsonify({"error": "PPTX 파일이 필요합니다."}), 400

        brand = json.loads(brand_json)
        pptx_bytes = pptx_file.read()

        from web_to_slide.pptx_builder import merge_cover
        merged = merge_cover(pptx_bytes, brand, headline, sub, logo_b64)

        return send_file(
            io.BytesIO(merged),
            mimetype='application/vnd.openxmlformats-officedocument.presentationml.presentation',
            as_attachment=True,
            download_name='merged_slides.pptx'
        )
    except Exception as e:
        _log(f"[merge-cover] Error: {e}")
        return jsonify({"error": "커버 병합 중 오류가 발생했습니다."}), 500


@api_bp.route("/api/active-job")
@login_required
def active_job():
    """현재 사용자의 진행 중인 작업 복원 — 새로고침 시 SSE 재연결"""
    _cleanup_stale_processing()
    user_id = session['user_id']
    db = get_db()
    row = db.execute(
        "SELECT job_id, url, status FROM generations WHERE user_id = ? AND status = 'processing' ORDER BY id DESC LIMIT 1",
        (user_id,)
    ).fetchone()
    if not row or not row['job_id']:
        return jsonify({"active": False})
    job_id = row['job_id']
    # Redis에서 실제 상태 확인 (result가 있을 때만 done 반환)
    if USE_CELERY:
        r = redis_client
        status = r.get(f'job:{job_id}:status')
        if status == 'done':
            result_raw = r.get(f'job:{job_id}:result')
            if not result_raw:
                return jsonify({"active": False})  # Redis TTL 만료 → 폼 표시
            return jsonify({"active": True, "job_id": job_id, "status": "done", "url": row['url']})
        elif status == 'error':
            return jsonify({"active": True, "job_id": job_id, "status": "error", "url": row['url']})
        elif status:
            return jsonify({"active": True, "job_id": job_id, "status": "running", "url": row['url']})
    return jsonify({"active": False})


@api_bp.route("/api/feedback", methods=["POST"])
def submit_feedback():
    """피드백 제출 (로그인 불필요 — 비회원도 가능)"""
    data = request.json or {}
    category = (data.get("category") or "").strip()
    message = (data.get("message") or "").strip()
    if not message:
        return jsonify({"error": "메시지를 입력해주세요."}), 400
    user_id = session.get("user_id")
    email = data.get("email", "")
    if not email and user_id:
        db = get_db()
        row = db.execute("SELECT email FROM users WHERE id = ?", (user_id,)).fetchone()
        email = row["email"] if row else ""
    db = get_db()
    db.execute(
        "INSERT INTO feedback (user_id, email, category, message, page_url) VALUES (?, ?, ?, ?, ?)",
        (user_id, email, category or "general", message, data.get("page_url", ""))
    )
    db.commit()
    return jsonify({"ok": True})


@api_bp.route("/api/convert-pdf", methods=["POST"])
@login_required
def convert_to_pdf():
    """PPTX 파일을 받아서 LibreOffice로 PDF 변환 후 반환"""
    if 'file' not in request.files:
        return jsonify({'error': 'PPTX 파일이 필요합니다'}), 400

    pptx_file = request.files['file']
    dl_name = request.form.get('filename', 'slides')

    with tempfile.TemporaryDirectory() as tmpdir:
        pptx_path = os.path.join(tmpdir, 'slides.pptx')
        pptx_file.save(pptx_path)

        try:
            result = subprocess.run(
                ['libreoffice', '--headless', '--convert-to', 'pdf',
                 '--outdir', tmpdir, pptx_path],
                capture_output=True, text=True, timeout=60
            )
        except FileNotFoundError:
            return jsonify({'error': 'LibreOffice가 설치되어 있지 않습니다. PPTX를 먼저 다운로드해 주세요.'}), 500
        except subprocess.TimeoutExpired:
            return jsonify({'error': 'PDF 변환 시간이 초과되었습니다.'}), 500

        if result.returncode != 0:
            return jsonify({'error': 'PDF 변환 실패', 'detail': result.stderr}), 500

        pdf_path = os.path.join(tmpdir, 'slides.pdf')
        if not os.path.exists(pdf_path):
            return jsonify({'error': 'PDF 파일이 생성되지 않았습니다.'}), 500

        # 로그인된 사용자면 직전 PDF 저장 (이전 파일 삭제 → 항상 1개만)
        import shutil, glob
        user_id = session.get('user_id')
        if user_id:
            user_pdf_dir = os.path.join(BASE_DIR, 'user_pdfs', str(user_id))
            os.makedirs(user_pdf_dir, exist_ok=True)
            # 이전 PDF 전부 삭제
            for old_pdf in glob.glob(os.path.join(user_pdf_dir, '*.pdf')):
                os.remove(old_pdf)
            # 새 PDF 저장 (원본 파일명)
            shutil.copy2(pdf_path, os.path.join(user_pdf_dir, dl_name + '.pdf'))

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=dl_name + '.pdf'
        )
