import csv
import io
from flask import Blueprint, request, jsonify, render_template, make_response
from web_to_slide.database import get_db, add_tokens, get_user_by_id
from routes import admin_required

admin_bp = Blueprint('admin', __name__)

@admin_bp.route("/admin")
@admin_required
def admin_page():
    return render_template("admin.html")

@admin_bp.route("/api/admin/stats")
@admin_required
def admin_stats():
    db = get_db()
    total_users = db.execute("SELECT COUNT(*) c FROM users").fetchone()['c']
    total_gens = db.execute("SELECT COUNT(*) c FROM generations").fetchone()['c']
    today_gens = db.execute(
        "SELECT COUNT(*) c FROM generations WHERE DATE(created_at) = DATE('now')"
    ).fetchone()['c']
    completed = db.execute(
        "SELECT COUNT(*) c FROM generations WHERE status = 'completed'"
    ).fetchone()['c']
    failed = db.execute(
        "SELECT COUNT(*) c FROM generations WHERE status = 'failed'"
    ).fetchone()['c']
    return jsonify({
        'total_users': total_users, 'total_generations': total_gens,
        'today_generations': today_gens, 'completed': completed, 'failed': failed,
        'success_rate': round(completed / max(total_gens, 1) * 100, 1)
    })

@admin_bp.route("/api/admin/users")
@admin_required
def admin_users():
    db = get_db()
    rows = db.execute(
        "SELECT u.id, u.email, u.name, u.tokens, u.created_at, u.last_login, "
        "(SELECT COUNT(*) FROM generations g WHERE g.user_id = u.id) as gen_count "
        "FROM users u ORDER BY u.created_at DESC LIMIT 100"
    ).fetchall()
    return jsonify({'users': [dict(r) for r in rows]})

@admin_bp.route("/api/admin/generations")
@admin_required
def admin_generations():
    db = get_db()
    rows = db.execute(
        "SELECT g.id, g.url, g.company_name, g.purpose, g.status, g.created_at, g.completed_at, "
        "u.email as user_email "
        "FROM generations g JOIN users u ON g.user_id = u.id "
        "ORDER BY g.created_at DESC LIMIT 100"
    ).fetchall()
    return jsonify({'generations': [dict(r) for r in rows]})

@admin_bp.route("/api/admin/add-tokens", methods=["POST"])
@admin_required
def admin_add_tokens():
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    amount = data.get('amount', 5)
    if not user_id:
        return jsonify({'error': 'user_id 필수'}), 400
    add_tokens(user_id, amount, 'admin_grant')
    user = get_user_by_id(user_id)
    return jsonify({'ok': True, 'tokens': user['tokens']})

@admin_bp.route("/api/admin/surveys")
@admin_required
def admin_surveys():
    db = get_db()
    rows = db.execute(
        "SELECT s.*, u.email FROM surveys s JOIN users u ON s.user_id = u.id ORDER BY s.created_at DESC"
    ).fetchall()
    return jsonify({"surveys": [dict(r) for r in rows]})

@admin_bp.route("/api/admin/surveys/csv")
@admin_required
def admin_surveys_csv():
    """설문 결과 CSV 다운로드 (엑셀 호환)"""
    db = get_db()
    rows = db.execute(
        "SELECT s.id, u.email, s.q1_industry, s.q2_role, s.q3_company_size, "
        "s.q4_frequency, s.q5_current_method, s.q6_payment_type, s.q7_price, "
        "s.q8_features, s.q9_feedback, s.created_at "
        "FROM surveys s JOIN users u ON s.user_id = u.id ORDER BY s.created_at DESC"
    ).fetchall()
    output = io.StringIO()
    output.write('\ufeff')  # BOM for Excel UTF-8
    writer = csv.writer(output)
    writer.writerow(['ID', '이메일', '업종', '직무', '회사규모', '제작빈도',
                     '기존방법', '결제방식', '가격', '희망기능', '자유의견', '참여일시'])
    for r in rows:
        writer.writerow([r['id'], r['email'], r['q1_industry'], r['q2_role'],
                         r['q3_company_size'], r['q4_frequency'], r['q5_current_method'],
                         r['q6_payment_type'], r['q7_price'], r['q8_features'],
                         r['q9_feedback'], r['created_at']])
    resp = make_response(output.getvalue())
    resp.headers['Content-Type'] = 'text/csv; charset=utf-8-sig'
    resp.headers['Content-Disposition'] = 'attachment; filename=tickdeck_surveys.csv'
    return resp

@admin_bp.route("/api/admin/feedback")
@admin_required
def admin_feedback():
    db = get_db()
    rows = db.execute(
        "SELECT f.id, f.email, f.category, f.message, f.page_url, f.created_at "
        "FROM feedback f ORDER BY f.created_at DESC LIMIT 100"
    ).fetchall()
    return jsonify([dict(r) for r in rows])
