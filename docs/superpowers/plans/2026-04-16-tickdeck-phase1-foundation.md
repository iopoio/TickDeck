# TickDeck Phase 1: 리포 기반 + FastAPI 스켈레톤 + DB + Auth

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `C:\Projects\Automation\TickDeck` 에 새 리포를 만들고, FastAPI 백엔드 스켈레톤 + PostgreSQL + Alembic + Google OAuth + JWT 인증까지 동작하는 기반을 구축한다.

**Architecture:** 모노리포 구조 (backend/ + frontend/ + worker/ + shared/). backend와 worker는 shared/를 `pip install -e ./shared`로 공유. FastAPI는 async SQLAlchemy 2.0 + Pydantic Settings로 환경변수 관리.

**Tech Stack:** Python 3.11+, FastAPI 0.111+, SQLAlchemy 2.0 (async), Alembic, PostgreSQL, python-jose (JWT), httpx, pytest-asyncio

---

## 파일 맵

```
C:\Projects\Automation\TickDeck\
├── .gitignore
├── .env.example
├── README.md
├── shared/
│   ├── pyproject.toml       ← pip install -e ./shared 진입점
│   └── shared/
│       └── __init__.py
├── backend/
│   ├── requirements.txt
│   ├── main.py              ← FastAPI 앱 + 미들웨어 등록
│   ├── core/
│   │   ├── config.py        ← Pydantic Settings (환경변수 로드)
│   │   ├── database.py      ← SQLAlchemy async engine + session
│   │   └── security.py      ← JWT 발급/검증
│   ├── models/
│   │   ├── base.py          ← DeclarativeBase
│   │   ├── user.py
│   │   ├── token.py
│   │   └── generation.py
│   ├── schemas/
│   │   ├── auth.py          ← 요청/응답 Pydantic 스키마
│   │   └── common.py
│   ├── routers/
│   │   ├── auth.py          ← Google OAuth 콜백 + JWT 발급
│   │   ├── slides.py        ← stub
│   │   ├── tokens.py        ← stub
│   │   └── history.py       ← stub
│   ├── middleware/
│   │   └── security_headers.py  ← OWASP 헤더
│   └── alembic/
│       ├── alembic.ini
│       ├── env.py
│       └── versions/
│           └── 0001_initial.py
└── tests/
    ├── conftest.py
    ├── test_health.py
    └── test_auth.py
```

---

## Task 1: 리포 초기화

**Files:**
- Create: `C:\Projects\Automation\TickDeck\.gitignore`
- Create: `C:\Projects\Automation\TickDeck\.env.example`
- Create: `C:\Projects\Automation\TickDeck\README.md`

- [ ] **Step 1: 폴더 생성 및 git 초기화**

```bash
mkdir -p C:/Projects/Automation/TickDeck
cd C:/Projects/Automation/TickDeck
git init
mkdir -p backend/core backend/models backend/schemas backend/routers backend/middleware backend/alembic/versions
mkdir -p shared/shared
mkdir -p worker/tasks
mkdir -p frontend
mkdir -p tests
```

- [ ] **Step 2: .gitignore 작성**

`C:\Projects\Automation\TickDeck\.gitignore`:
```
# Python
__pycache__/
*.py[cod]
*.egg-info/
.venv/
venv/
dist/
build/
*.egg

# Env
.env
.env.local
.env.*.local

# Node
node_modules/
dist/
.vite/

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Generated
alembic/versions/*.pyc
*.pptx
*.pdf
tmp/
```

- [ ] **Step 3: .env.example 작성**

`C:\Projects\Automation\TickDeck\.env.example`:
```
# Database
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/tickdeck

# JWT
SECRET_KEY=your-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
JWT_REFRESH_EXPIRE_DAYS=30

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
GOOGLE_REDIRECT_URI=http://localhost:8000/api/auth/callback

# Redis
REDIS_URL=redis://localhost:6379/0

# Frontend
FRONTEND_URL=http://localhost:5173

# Gemini
GEMINI_API_KEY=your-gemini-api-key

# Admin
ADMIN_EMAIL=your-admin-email@gmail.com
```

- [ ] **Step 4: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add .
git commit -m "chore: 리포 초기화 + .gitignore + .env.example"
```

---

## Task 2: shared/ 패키지 초기화

**Files:**
- Create: `shared/pyproject.toml`
- Create: `shared/shared/__init__.py`

- [ ] **Step 1: pyproject.toml 작성**

`C:\Projects\Automation\TickDeck\shared\pyproject.toml`:
```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.backends.legacy:build"

[project]
name = "tickdeck-shared"
version = "0.1.0"
description = "TickDeck 공유 서비스 (crawler, gemini, pptx_builder)"
requires-python = ">=3.11"
dependencies = []

[tool.setuptools.packages.find]
where = ["."]
include = ["shared*"]
```

- [ ] **Step 2: __init__.py 작성**

`C:\Projects\Automation\TickDeck\shared\shared\__init__.py`:
```python
"""TickDeck 공유 서비스 패키지"""
```

- [ ] **Step 3: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add shared/
git commit -m "chore: shared/ 패키지 초기화"
```

---

## Task 3: backend/ requirements.txt + Pydantic Settings

**Files:**
- Create: `backend/requirements.txt`
- Create: `backend/core/config.py`

- [ ] **Step 1: requirements.txt 작성**

`C:\Projects\Automation\TickDeck\backend\requirements.txt`:
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
pydantic==2.7.0
pydantic-settings==2.2.1
sqlalchemy[asyncio]==2.0.30
asyncpg==0.29.0
alembic==1.13.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
httpx==0.27.0
python-multipart==0.0.9
redis==5.0.4
celery==5.4.0
slowapi==0.1.9
pytest==8.2.0
pytest-asyncio==0.23.6
httpx==0.27.0
```

- [ ] **Step 2: 가상환경 생성 + 설치**

```bash
cd C:/Projects/Automation/TickDeck/backend
python -m venv .venv
.venv/Scripts/activate   # Windows
pip install -r requirements.txt
pip install -e ../shared
```

- [ ] **Step 3: core/config.py 작성**

`C:\Projects\Automation\TickDeck\backend\core\config.py`:
```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file="../.env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Database
    database_url: str

    # JWT
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    jwt_refresh_expire_days: int = 30

    # Google OAuth
    google_client_id: str
    google_client_secret: str
    google_redirect_uri: str

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Frontend
    frontend_url: str = "http://localhost:5173"

    # Gemini
    gemini_api_key: str

    # Admin
    admin_email: str


settings = Settings()
```

- [ ] **Step 4: .env 파일 생성 (.env.example 복사 후 실제 값 입력)**

```bash
cd C:/Projects/Automation/TickDeck
cp .env.example .env
# .env 파일에 실제 값 입력 (DATABASE_URL, SECRET_KEY, GOOGLE_CLIENT_ID 등)
```

⚠️ .env는 .gitignore에 포함됨. 절대 커밋 금지.

- [ ] **Step 5: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add backend/requirements.txt backend/core/config.py
git commit -m "feat: backend 의존성 + Pydantic Settings 설정"
```

---

## Task 4: Database 연결 + 모델 정의

**Files:**
- Create: `backend/core/database.py`
- Create: `backend/models/base.py`
- Create: `backend/models/user.py`
- Create: `backend/models/token.py`
- Create: `backend/models/generation.py`

- [ ] **Step 1: core/database.py 작성**

`C:\Projects\Automation\TickDeck\backend\core\database.py`:
```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from backend.core.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 2: models/base.py 작성**

`C:\Projects\Automation\TickDeck\backend\models\base.py`:
```python
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass
```

- [ ] **Step 3: models/user.py 작성**

`C:\Projects\Automation\TickDeck\backend\models\user.py`:
```python
from datetime import datetime
from sqlalchemy import String, DateTime, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    picture: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 4: models/token.py 작성**

`C:\Projects\Automation\TickDeck\backend\models\token.py`:
```python
from datetime import datetime
from sqlalchemy import Integer, ForeignKey, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base


class TokenBalance(Base):
    __tablename__ = "token_balances"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    balance: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class TokenTransaction(Base):
    __tablename__ = "token_transactions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    # 타입: signup_bonus / generation_lock / generation_confirm / generation_refund / survey_reward
    transaction_type: Mapped[str] = mapped_column(String(50), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # 양수=충전, 음수=차감
    note: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 5: models/generation.py 작성**

`C:\Projects\Automation\TickDeck\backend\models\generation.py`:
```python
from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from backend.models.base import Base


class Generation(Base):
    __tablename__ = "generations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID4
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    language: Mapped[str] = mapped_column(String(2), default="ko")  # ko / en
    # 상태: pending / crawling / structuring / ready_to_edit / building_pptx / converting_pdf / done / failed
    status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    pptx_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    pdf_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    slide_json: Mapped[str | None] = mapped_column(Text, nullable=True)  # Gemini 생성 JSON
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

- [ ] **Step 6: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add backend/core/database.py backend/models/
git commit -m "feat: DB 연결 설정 + User/Token/Generation 모델 정의"
```

---

## Task 5: Alembic 초기화 + 첫 마이그레이션

**Files:**
- Create: `backend/alembic.ini`
- Modify: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial.py`

- [ ] **Step 1: Alembic 초기화**

```bash
cd C:/Projects/Automation/TickDeck/backend
alembic init alembic
```

- [ ] **Step 2: alembic.ini의 sqlalchemy.url 주석 처리**

`backend/alembic.ini` 에서 아래 줄을 찾아 주석 처리:
```ini
# sqlalchemy.url = driver://user:pass@localhost/dbname
```
(env.py에서 동적으로 로드할 것이므로)

- [ ] **Step 3: alembic/env.py 수정 (async 지원)**

`C:\Projects\Automation\TickDeck\backend\alembic\env.py`:
```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 모델 임포트 (자동 감지용)
from backend.models.base import Base
from backend.models.user import User        # noqa
from backend.models.token import TokenBalance, TokenTransaction  # noqa
from backend.models.generation import Generation  # noqa
from backend.core.config import settings

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations():
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online():
    asyncio.run(run_async_migrations())


run_migrations_online()
```

- [ ] **Step 4: PostgreSQL DB 생성 확인**

```bash
# PostgreSQL이 설치/실행 중인지 확인
psql -U postgres -c "CREATE DATABASE tickdeck;"
# 또는 기존 DO PostgreSQL 연결 정보 .env에 입력
```

- [ ] **Step 5: 첫 마이그레이션 생성 + 실행**

```bash
cd C:/Projects/Automation/TickDeck/backend
alembic revision --autogenerate -m "initial"
alembic upgrade head
```

예상 출력:
```
INFO  [alembic.runtime.migration] Running upgrade  -> xxxx, initial
```

- [ ] **Step 6: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add backend/alembic.ini backend/alembic/
git commit -m "feat: Alembic 설정 + 초기 DB 마이그레이션"
```

---

## Task 6: JWT 보안 + Health Check 엔드포인트

**Files:**
- Create: `backend/core/security.py`
- Create: `backend/schemas/common.py`
- Create: `backend/main.py`
- Create: `tests/conftest.py`
- Create: `tests/test_health.py`

- [ ] **Step 1: 테스트 먼저 작성**

`C:\Projects\Automation\TickDeck\tests\test_health.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd C:/Projects/Automation/TickDeck/backend
pytest ../tests/test_health.py -v
```

예상: `ImportError: cannot import name 'app' from 'backend.main'` (main.py 없으므로)

- [ ] **Step 3: core/security.py 작성**

`C:\Projects\Automation\TickDeck\backend\core\security.py`:
```python
from datetime import datetime, timedelta
from typing import Any
from jose import JWTError, jwt
from backend.core.config import settings


def create_access_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def create_refresh_token(data: dict[str, Any]) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.jwt_refresh_expire_days)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_token(token: str) -> dict[str, Any]:
    """토큰 디코드. 유효하지 않으면 JWTError 발생."""
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
```

- [ ] **Step 4: schemas/common.py 작성**

`C:\Projects\Automation\TickDeck\backend\schemas\common.py`:
```python
from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str


class ErrorResponse(BaseModel):
    detail: str
```

- [ ] **Step 5: main.py 작성**

`C:\Projects\Automation\TickDeck\backend\main.py`:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.schemas.common import HealthResponse

app = FastAPI(title="TickDeck API", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: conftest.py 작성**

`C:\Projects\Automation\TickDeck\tests\conftest.py`:
```python
import pytest
import asyncio


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

- [ ] **Step 7: 테스트 통과 확인**

```bash
cd C:/Projects/Automation/TickDeck/backend
pytest ../tests/test_health.py -v
```

예상:
```
tests/test_health.py::test_health_check PASSED
1 passed in X.XXs
```

- [ ] **Step 8: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add backend/core/security.py backend/schemas/common.py backend/main.py tests/
git commit -m "feat: JWT 유틸 + FastAPI 앱 + health check 엔드포인트"
```

---

## Task 7: Google OAuth + JWT 발급 라우터

**Files:**
- Create: `backend/schemas/auth.py`
- Create: `backend/routers/auth.py`
- Create: `tests/test_auth.py`

- [ ] **Step 1: 테스트 먼저 작성**

`C:\Projects\Automation\TickDeck\tests\test_auth.py`:
```python
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app


@pytest.mark.asyncio
async def test_auth_google_redirect():
    """Google OAuth 로그인 URL로 리다이렉트 확인"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/google", follow_redirects=False)
    assert response.status_code == 307
    assert "accounts.google.com" in response.headers["location"]


@pytest.mark.asyncio
async def test_auth_me_unauthorized():
    """토큰 없이 /me 접근 시 401"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/me")
    assert response.status_code == 401
```

- [ ] **Step 2: 테스트 실패 확인**

```bash
cd C:/Projects/Automation/TickDeck/backend
pytest ../tests/test_auth.py -v
```

예상: `FAILED - 404 (라우터 미등록)`

- [ ] **Step 3: schemas/auth.py 작성**

`C:\Projects\Automation\TickDeck\backend\schemas\auth.py`:
```python
from pydantic import BaseModel


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str
    name: str
    picture: str | None
    is_admin: bool

    model_config = {"from_attributes": True}
```

- [ ] **Step 4: routers/auth.py 작성**

`C:\Projects\Automation\TickDeck\backend\routers\auth.py`:
```python
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import httpx

from backend.core.config import settings
from backend.core.database import get_db
from backend.core.security import create_access_token, create_refresh_token, decode_token
from backend.models.user import User
from backend.models.token import TokenBalance, TokenTransaction
from backend.schemas.auth import TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"


@router.get("/google")
async def google_login():
    """Google OAuth 로그인 URL로 리다이렉트"""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": settings.google_redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
    }
    query = "&".join(f"{k}={v}" for k, v in params.items())
    return RedirectResponse(f"{GOOGLE_AUTH_URL}?{query}")


@router.get("/callback", response_model=TokenResponse)
async def google_callback(code: str, db: AsyncSession = Depends(get_db)):
    """Google 콜백: code → 유저 정보 → JWT 발급"""
    async with httpx.AsyncClient() as client:
        # 1. code → access_token 교환
        token_resp = await client.post(GOOGLE_TOKEN_URL, data={
            "code": code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        })
        token_data = token_resp.json()

        # 2. access_token → 유저 정보
        userinfo_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {token_data['access_token']}"},
        )
        userinfo = userinfo_resp.json()

    # 3. DB에서 유저 조회 또는 생성
    result = await db.execute(select(User).where(User.email == userinfo["email"]))
    user = result.scalar_one_or_none()

    if user is None:
        # 신규 유저: 생성 + 가입 보너스 2토큰
        user = User(
            email=userinfo["email"],
            name=userinfo.get("name", ""),
            picture=userinfo.get("picture"),
            is_admin=(userinfo["email"] == settings.admin_email),
        )
        db.add(user)
        await db.flush()  # user.id 확보

        balance = TokenBalance(user_id=user.id, balance=2)
        db.add(balance)

        tx = TokenTransaction(
            user_id=user.id,
            transaction_type="signup_bonus",
            amount=2,
            note="가입 보너스",
        )
        db.add(tx)
        await db.commit()
        await db.refresh(user)
    else:
        await db.commit()

    # 4. JWT 발급
    payload = {"sub": str(user.id), "email": user.email}
    return TokenResponse(
        access_token=create_access_token(payload),
        refresh_token=create_refresh_token(payload),
    )


async def get_current_user(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> User:
    """JWT에서 현재 유저 추출 (Depends용)"""
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user


@router.get("/me", response_model=UserResponse)
async def get_me(
    authorization: str = "",
    db: AsyncSession = Depends(get_db),
):
    """현재 로그인 유저 정보"""
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header required")
    token = authorization.split(" ")[1]
    user = await get_current_user(token, db)
    return user
```

- [ ] **Step 5: main.py에 라우터 등록**

`backend/main.py` 수정:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.schemas.common import HealthResponse
from backend.routers import auth  # 추가

app = FastAPI(title="TickDeck API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)  # 추가


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 6: 테스트 통과 확인**

```bash
cd C:/Projects/Automation/TickDeck/backend
pytest ../tests/test_auth.py -v
```

예상:
```
tests/test_auth.py::test_auth_google_redirect PASSED
tests/test_auth.py::test_auth_me_unauthorized PASSED
2 passed in X.XXs
```

- [ ] **Step 7: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add backend/routers/auth.py backend/schemas/auth.py backend/main.py tests/test_auth.py
git commit -m "feat: Google OAuth 콜백 + JWT 발급 + /me 엔드포인트"
```

---

## Task 8: stub 라우터 + OWASP 보안 헤더

**Files:**
- Create: `backend/routers/slides.py`
- Create: `backend/routers/tokens.py`
- Create: `backend/routers/history.py`
- Create: `backend/middleware/security_headers.py`

- [ ] **Step 1: stub 라우터 3개 작성**

`C:\Projects\Automation\TickDeck\backend\routers\slides.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/slides", tags=["slides"])


@router.post("/generate")
async def generate_slide():
    """슬라이드 생성 요청 (Phase 3에서 구현)"""
    return {"message": "coming soon"}
```

`C:\Projects\Automation\TickDeck\backend\routers\tokens.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/tokens", tags=["tokens"])


@router.get("/balance")
async def get_balance():
    """토큰 잔액 조회 (Phase 3에서 구현)"""
    return {"balance": 0}
```

`C:\Projects\Automation\TickDeck\backend\routers\history.py`:
```python
from fastapi import APIRouter

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("/")
async def list_history():
    """생성 이력 (Phase 4에서 구현)"""
    return {"items": []}
```

- [ ] **Step 2: 보안 헤더 미들웨어 작성**

`C:\Projects\Automation\TickDeck\backend\middleware\security_headers.py`:
```python
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response
```

- [ ] **Step 3: main.py에 모두 등록**

`backend/main.py` 최종:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings
from backend.schemas.common import HealthResponse
from backend.routers import auth, slides, tokens, history
from backend.middleware.security_headers import SecurityHeadersMiddleware

app = FastAPI(title="TickDeck API", version="1.0.0")

# 보안 헤더
app.add_middleware(SecurityHeadersMiddleware)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 라우터
app.include_router(auth.router)
app.include_router(slides.router)
app.include_router(tokens.router)
app.include_router(history.router)


@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    return {"status": "ok"}
```

- [ ] **Step 4: 전체 테스트 통과 확인**

```bash
cd C:/Projects/Automation/TickDeck/backend
pytest ../tests/ -v
```

예상:
```
tests/test_health.py::test_health_check PASSED
tests/test_auth.py::test_auth_google_redirect PASSED
tests/test_auth.py::test_auth_me_unauthorized PASSED
3 passed in X.XXs
```

- [ ] **Step 5: 서버 실행 확인**

```bash
cd C:/Projects/Automation/TickDeck/backend
uvicorn main:app --reload --port 8000
```

브라우저에서 `http://localhost:8000/docs` 접속 → FastAPI 자동 문서 확인

- [ ] **Step 6: 커밋**

```bash
cd C:/Projects/Automation/TickDeck
git add backend/routers/ backend/middleware/ backend/main.py
git commit -m "feat: stub 라우터 3개 + OWASP 보안 헤더 미들웨어"
```

---

## Phase 1 완료 체크리스트

```
✅ 리포 초기화 (git, .gitignore, .env.example)
✅ shared/ 패키지 구조
✅ FastAPI 앱 실행 (uvicorn)
✅ Pydantic Settings 환경변수 관리
✅ PostgreSQL 연결 + SQLAlchemy async
✅ Alembic 마이그레이션
✅ User / TokenBalance / TokenTransaction / Generation 모델
✅ JWT 발급/검증 유틸
✅ Google OAuth 콜백 + 신규 유저 가입 보너스
✅ /api/health 엔드포인트
✅ /api/auth/me 보호 엔드포인트
✅ stub 라우터 3개 (slides, tokens, history)
✅ OWASP 보안 헤더 미들웨어
✅ CORS 설정
✅ 테스트 3개 통과
```

## 다음 단계

Phase 2: shared/ 서비스 포팅
- `docs/superpowers/plans/2026-04-16-tickdeck-phase2-shared-services.md`
- Playwright 크롤러, Gemini + Pydantic 검증, color_resolver, python-pptx 레이아웃 포팅
