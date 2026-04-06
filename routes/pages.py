from flask import Blueprint, render_template, make_response, send_from_directory
from routes import admin_required
from i18n import T_KO, T_EN
from pathlib import Path

pages_bp = Blueprint('pages', __name__)
BASE_DIR = Path(__file__).parent.parent

@pages_bp.route("/")
def landing():
    """준비 중 페이지 (일반 공개)"""
    return render_template("coming_soon.html")

@pages_bp.route("/app")
@admin_required
def app_page():
    """앱 페이지 — 관리자만 접근 가능"""
    resp = make_response(render_template("index.html", lang="ko", t=T_KO))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp

@pages_bp.route("/en")
def landing_en():
    """EN 준비 중"""
    return render_template("coming_soon.html")

@pages_bp.route("/en/app")
@admin_required
def app_page_en():
    """EN 앱 — 관리자만"""
    resp = make_response(render_template("index.html", lang="en", t=T_EN))
    resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    return resp

@pages_bp.route("/static/<path:filename>")
def serve_static(filename):
    """static 폴더 파일 서빙 (stitch_templates.json 등)"""
    static_dir = BASE_DIR / "static"
    return send_from_directory(static_dir, filename)

@pages_bp.route("/robots.txt")
def robots_txt():
    return send_from_directory(BASE_DIR / "static", "robots.txt", mimetype="text/plain")

@pages_bp.route("/sitemap.xml")
def sitemap_xml():
    return send_from_directory(BASE_DIR / "static", "sitemap.xml", mimetype="application/xml")
