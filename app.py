"""
app.py — WebToSlide 로컬 웹 서버
localhost:5000 에서 슬라이드 생성 UI 제공
"""
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from pathlib import Path

# Windows cp949 환경에서 이모지·유니코드 출력 오류 방지
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace', line_buffering=True)

# 로그 파일 — OneDrive 외부 경로로 저장 (한글 경로 잠금 회피)
_LOG_PATH_CANDIDATES = [
    os.path.join(os.path.expanduser('~'), 'webtoslide_server.log'),  # C:\Users\chaej\webtoslide_server.log
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'server.log'),  # 원래 경로 (fallback)
]
_LOG_PATH = _LOG_PATH_CANDIDATES[0]

def _log(msg: str):
    """파일 + stdout에 기록"""
    line = msg + '\n'
    # 터미널 출력 (print → stdout, 가장 안정적)
    try:
        print(msg, flush=True)
    except Exception:
        pass
    # 파일 기록
    for _path in _LOG_PATH_CANDIDATES:
        try:
            with open(_path, 'a', encoding='utf-8') as _f:
                _f.write(line)
            break  # 첫 번째 성공하면 중단
        except Exception:
            continue

from flask import Flask, jsonify, make_response, render_template, request, Response, send_file, send_from_directory

BASE_DIR = Path(__file__).parent
sys.path.insert(0, str(BASE_DIR))

from web_to_slide.pipeline import run_pipeline

app = Flask(__name__)
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB
app.jinja_env.auto_reload = True

# job_id → { status, lines, result, error }
JOBS: dict[str, dict] = {}


# ── 파이프라인 실행 ─────────────────────────────────────────────────────────
def _run(job_id: str, url: str, company: str,
         narrative_type: str = "auto", mood: str = "professional", purpose: str = "brand",
         brand_color: str = ""):
    job = JOBS[job_id]

    def on_progress(line: str):
        if line.strip():
            job["lines"].append(line)
            _log(line)

    import os, re as _re
    def _clear_cache(co):
        _slug = _re.sub(r'[^\w]', '', (co or '').lower())[:20]
        for _cf in [f"slide_{_slug}_text.json", f"slide_{_slug}_img.json", f"slide_{_slug}.json"]:
            try:
                if os.path.exists(_cf):
                    os.remove(_cf)
                    on_progress(f"  → 캐시 삭제: {_cf}")
            except Exception:
                pass

    try:
        result = run_pipeline(url, company or None, progress_fn=on_progress,
                              narrative_type=narrative_type, mood=mood, purpose=purpose,
                              brand_color=brand_color)
        job["result"] = result
        job["status"] = "done"
    except Exception as e:
        import traceback as _tb
        err_str = str(e)
        for _tl in _tb.format_exc().splitlines():
            on_progress(f"  TB| {_tl}")
        on_progress(f"  ⚠ 오류 발생: {err_str}")
        _slug = _re.sub(r'[^\w]', '', (company or url.split('//')[-1].split('/')[0].replace('.', '')).lower())[:20]
        _clear_cache(_slug)
        on_progress("  → 캐시 삭제 후 재시도 중...")
        try:
            result = run_pipeline(url, company or None, progress_fn=on_progress,
                                  narrative_type=narrative_type, mood=mood, purpose=purpose,
                                  brand_color=brand_color)
            job["result"] = result
            job["status"] = "done"
        except Exception as e2:
            import traceback as _tb2
            _log("=== TRACEBACK2 ===\n" + _tb2.format_exc() + "=================")
            job["status"] = "error"
            job["error"] = str(e2)


# ── 라우트 ──────────────────────────────────────────────────────────────────
@app.route("/")
def index():
    resp = make_response(render_template("index.html"))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp


@app.route("/generate", methods=["POST"])
def generate():
    data    = request.get_json(force=True)
    url            = (data.get("url") or "").strip()
    company        = (data.get("company") or "").strip()
    narrative_type = (data.get("narrative_type") or "auto").strip()
    mood           = (data.get("mood") or "professional").strip()
    purpose        = (data.get("purpose") or "auto").strip()
    brand_color    = (data.get("brand_color") or "").strip()

    if not url:
        return jsonify({"error": "URL을 입력하세요."}), 400

    if not url.startswith("http"):
        url = "https://" + url

    job_id = str(uuid.uuid4())
    JOBS[job_id] = {"status": "running", "lines": [], "result": None, "error": None}

    t = threading.Thread(target=_run, args=(job_id, url, company, narrative_type, mood, purpose, brand_color), daemon=True)
    t.start()

    return jsonify({"job_id": job_id})


@app.route("/stream/<job_id>")
def stream(job_id: str):
    """Server-Sent Events — 실시간 로그 + 완료 이벤트"""
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


@app.route("/clear-cache", methods=["POST"])
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


@app.route("/result/<job_id>")
def result(job_id: str):
    """완료된 작업의 JSON 결과 반환 (슬라이드 데이터 전체)"""
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"error": "존재하지 않는 작업입니다."}), 404
    if job["status"] != "done":
        return jsonify({"error": "작업이 아직 완료되지 않았습니다.", "status": job["status"]}), 202
    return jsonify(job["result"])


@app.route("/static/<path:filename>")
def serve_static(filename):
    """static 폴더 파일 서빙 (stitch_templates.json 등)"""
    static_dir = BASE_DIR / "static"
    return send_from_directory(static_dir, filename)


@app.route("/api/convert-pdf", methods=["POST"])
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

        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=dl_name + '.pdf'
        )


if __name__ == "__main__":
    print("=" * 50)
    print("  TickDeck 서버 시작")
    print("  http://localhost:5000")
    print(f"  로그 파일: {_LOG_PATH}")
    print("=" * 50)
    _log("=== WebToSlide 서버 시작 ===")
    app.run(host='0.0.0.0', debug=False, port=5000, threaded=True)
