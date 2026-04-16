# TickDeck

URL 입력 → 슬라이드 자동 생성 서비스

## Stack
- Backend: FastAPI + SQLAlchemy async + Alembic
- Frontend: React + Vite + Tailwind CSS
- Worker: Celery + Redis
- DB: PostgreSQL
- Auth: Google OAuth + JWT

## Setup

```bash
cp .env.example .env
# .env 파일에 실제 값 입력

cd backend
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements.txt
pip install -e ../shared
```

## 실행

```bash
# 백엔드
cd backend && uvicorn main:app --reload

# 프론트엔드
cd frontend && npm install && npm run dev

# 워커
cd backend && celery -A worker.celery_app worker --loglevel=info
```
