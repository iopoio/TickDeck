"""
database.py — TickDeck SQLite DB 모듈
- 사용자 인증 + 토큰 시스템
- WAL 모드로 concurrent read 성능 확보
"""

import sqlite3
import os
from flask import g, current_app

DB_FILENAME = 'tickdeck.db'

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    email         TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    name          TEXT,
    tokens        INTEGER DEFAULT 2,
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    last_login    DATETIME
);

CREATE TABLE IF NOT EXISTS generations (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    url           TEXT NOT NULL,
    company_name  TEXT,
    purpose       TEXT,
    status        TEXT DEFAULT 'pending',
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
    completed_at  DATETIME
);

CREATE TABLE IF NOT EXISTS surveys (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id         INTEGER NOT NULL REFERENCES users(id),
    q1_industry     TEXT,
    q2_role         TEXT,
    q3_company_size TEXT,
    q4_frequency    TEXT,
    q5_current_method TEXT,
    q6_payment_type TEXT,
    q7_price        TEXT,
    q8_features     TEXT,
    q9_feedback     TEXT,
    created_at      DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS token_history (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id       INTEGER NOT NULL REFERENCES users(id),
    amount        INTEGER NOT NULL,
    reason        TEXT NOT NULL,
    generation_id INTEGER REFERENCES generations(id),
    created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
);
"""


def _get_db_path():
    """instance 폴더 내 DB 경로"""
    instance_path = current_app.instance_path
    os.makedirs(instance_path, exist_ok=True)
    return os.path.join(instance_path, DB_FILENAME)


def get_db():
    """요청 내 SQLite 연결 반환 (g 객체에 캐싱)"""
    if 'db' not in g:
        g.db = sqlite3.connect(_get_db_path())
        g.db.row_factory = sqlite3.Row  # dict-like 접근
        g.db.execute("PRAGMA journal_mode=WAL")
        g.db.execute("PRAGMA foreign_keys=ON")
    return g.db


def close_db(e=None):
    """요청 종료 시 연결 닫기"""
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    """스키마 생성 (테이블 없으면 자동 생성)"""
    db = get_db()
    db.executescript(SCHEMA_SQL)
    db.commit()


def init_app(app):
    """Flask 앱에 DB 훅 등록"""
    app.teardown_appcontext(close_db)

    @app.cli.command('init-db')
    def init_db_command():
        """flask init-db 명령으로 DB 초기화"""
        with app.app_context():
            init_db()
            print(f"DB 초기화 완료: {_get_db_path()}")


# ── 헬퍼 함수 ─────────────────────────────────────

def create_user(email, password_hash, name=None):
    """사용자 생성 + 가입 토큰 2개 지급 → user_id 반환"""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO users (email, password_hash, name) VALUES (?, ?, ?)",
        (email, password_hash, name)
    )
    user_id = cursor.lastrowid
    # 가입 토큰 지급 내역
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason) VALUES (?, 2, 'signup')",
        (user_id,)
    )
    db.commit()
    return user_id


def get_user_by_email(email):
    """이메일로 사용자 조회 → Row or None"""
    db = get_db()
    return db.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()


def get_user_by_id(user_id):
    """ID로 사용자 조회 → Row or None"""
    db = get_db()
    return db.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()


def update_last_login(user_id):
    """마지막 로그인 시간 갱신"""
    db = get_db()
    db.execute("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?", (user_id,))
    db.commit()


def deduct_token(user_id, generation_id=None):
    """토큰 1개 차감 → 성공 True, 부족 False"""
    db = get_db()
    user = db.execute("SELECT tokens FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user['tokens'] < 1:
        return False
    db.execute("UPDATE users SET tokens = tokens - 1 WHERE id = ?", (user_id,))
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason, generation_id) VALUES (?, -1, 'generate', ?)",
        (user_id, generation_id)
    )
    db.commit()
    return True


def check_and_deduct_token(user_id):
    """토큰 1개 차감. 성공 시 남은 토큰 수 반환, 부족 시 None."""
    db = get_db()
    user = db.execute("SELECT tokens FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user or user['tokens'] < 1:
        return None
    db.execute("UPDATE users SET tokens = tokens - 1 WHERE id = ?", (user_id,))
    db.commit()
    remaining = db.execute("SELECT tokens FROM users WHERE id = ?", (user_id,)).fetchone()['tokens']
    return remaining


def refund_token(user_id, generation_id=None):
    """실패 시 토큰 1개 환불"""
    db = get_db()
    db.execute("UPDATE users SET tokens = tokens + 1 WHERE id = ?", (user_id,))
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason, generation_id) VALUES (?, 1, 'refund_failed', ?)",
        (user_id, generation_id)
    )
    db.commit()


def add_tokens(user_id, amount, reason='purchase'):
    """토큰 추가 (구매, 관리자 지급 등)"""
    db = get_db()
    db.execute("UPDATE users SET tokens = tokens + ? WHERE id = ?", (amount, user_id))
    db.execute(
        "INSERT INTO token_history (user_id, amount, reason) VALUES (?, ?, ?)",
        (user_id, amount, reason)
    )
    db.commit()


def create_generation(user_id, url, company_name=None, purpose='auto'):
    """생성 기록 추가 → generation_id 반환"""
    db = get_db()
    cursor = db.execute(
        "INSERT INTO generations (user_id, url, company_name, purpose) VALUES (?, ?, ?, ?)",
        (user_id, url, company_name, purpose)
    )
    db.commit()
    return cursor.lastrowid


def complete_generation(generation_id, status='completed'):
    """생성 완료/실패 기록"""
    db = get_db()
    db.execute(
        "UPDATE generations SET status = ?, completed_at = CURRENT_TIMESTAMP WHERE id = ?",
        (status, generation_id)
    )
    db.commit()
