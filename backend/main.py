import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'shared'))

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
