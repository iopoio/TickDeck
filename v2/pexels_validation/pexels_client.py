"""Pexels 사진 검색·다운로드 클라이언트 (TickDeck v2 사진 마땅함 검증용).

목적: TickDeck 데모 PDF의 사진 placeholder를 Pexels 스톡으로 채울 수 있는가 검증.
"Pexels 연동"이 목적이 아니라 "후추님 안목 기준에 마땅한 사진을 주는가" 판정이 목적.

설계 원칙
- API key 하드코딩 X. os.environ 또는 .env 파일에서 로드 (investlab 패턴).
- 슬라이드 톤(다크/라이트)·비율(orientation)·고화질 필터 반영.
- WebToSlide 본체 코드는 _env_handoff에 .env만 있고 소스 없음 → Pexels REST 직접 구현.
"""
from __future__ import annotations

import hashlib
import os
from dataclasses import dataclass
from pathlib import Path

import requests

PEXELS_SEARCH_URL = "https://api.pexels.com/v1/search"
DEFAULT_TIMEOUT = 25


def load_pexels_key(env_path: str | None = None) -> str:
    """PEXELS_API_KEY를 환경변수 우선, 없으면 지정한 .env에서 로드.

    하드코딩 절대 금지. 호출부가 키 값을 직접 다루지 않도록 캡슐화.
    """
    key = os.environ.get("PEXELS_API_KEY")
    if key:
        return key.strip()
    if env_path and Path(env_path).exists():
        for line in Path(env_path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("PEXELS_API_KEY"):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError(
        "PEXELS_API_KEY를 찾지 못함. 환경변수 또는 .env 경로를 확인하세요."
    )


@dataclass
class PexelsPhoto:
    id: int
    width: int
    height: int
    avg_color: str
    alt: str
    photographer: str
    url: str  # 페이지 URL (출처 표기용)
    src_original: str
    src_large2x: str
    src_large: str

    @property
    def aspect(self) -> float:
        return self.width / self.height if self.height else 0.0

    @property
    def is_dark(self) -> bool:
        """avg_color(#RRGGBB) 밝기로 다크/라이트 판정 (0~255 luma)."""
        try:
            c = self.avg_color.lstrip("#")
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            luma = 0.2126 * r + 0.7152 * g + 0.0722 * b
            return luma < 96  # 어두운 편
        except Exception:
            return False

    @property
    def luma(self) -> float:
        try:
            c = self.avg_color.lstrip("#")
            r, g, b = int(c[0:2], 16), int(c[2:4], 16), int(c[4:6], 16)
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        except Exception:
            return 128.0


class PexelsClient:
    def __init__(self, api_key: str):
        self._key = api_key
        self._session = requests.Session()
        self._session.headers.update({"Authorization": api_key})

    def search(
        self,
        query: str,
        *,
        orientation: str = "landscape",  # landscape | portrait | square
        size: str = "large",  # large(24MP+) | medium | small
        per_page: int = 12,
        page: int = 1,
    ) -> tuple[list[PexelsPhoto], dict]:
        params = {
            "query": query,
            "orientation": orientation,
            "size": size,
            "per_page": per_page,
            "page": page,
        }
        r = self._session.get(PEXELS_SEARCH_URL, params=params, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        photos = []
        for p in data.get("photos", []):
            src = p.get("src", {})
            photos.append(
                PexelsPhoto(
                    id=p["id"],
                    width=p["width"],
                    height=p["height"],
                    avg_color=p.get("avg_color", "#808080"),
                    alt=p.get("alt", "") or "",
                    photographer=p.get("photographer", ""),
                    url=p.get("url", ""),
                    src_original=src.get("original", ""),
                    src_large2x=src.get("large2x", ""),
                    src_large=src.get("large", ""),
                )
            )
        meta = {
            "total_results": data.get("total_results"),
            "rate_remaining": r.headers.get("X-Ratelimit-Remaining"),
        }
        return photos, meta

    def download(self, photo: PexelsPhoto, cache_dir: str, prefer: str = "large2x") -> str:
        """고화질 이미지 다운로드(캐시). prefer: original|large2x|large."""
        url = {
            "original": photo.src_original,
            "large2x": photo.src_large2x,
            "large": photo.src_large,
        }.get(prefer, photo.src_large2x) or photo.src_large
        Path(cache_dir).mkdir(parents=True, exist_ok=True)
        h = hashlib.md5(url.encode()).hexdigest()[:12]
        out = Path(cache_dir) / f"pexels_{photo.id}_{h}.jpg"
        if out.exists() and out.stat().st_size > 0:
            return str(out)
        resp = self._session.get(url, timeout=DEFAULT_TIMEOUT)
        resp.raise_for_status()
        out.write_bytes(resp.content)
        return str(out)
