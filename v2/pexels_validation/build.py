"""TickDeck 데모 PDF placeholder를 Pexels 사진으로 채운 after PDF 생성 + 검증 데이터.

흐름
  1. placeholders.py 의 각 슬롯에 대해 Pexels 검색 (톤·비율·고화질 필터)
  2. 톤 매칭 점수로 후보 정렬 → 최선 1장 선택
  3. 비율 유지 crop (왜곡 0) 후 PDF 박스에 삽입 → *_pexels_after.pdf
  4. search_spec.json (검색 방식 명세) + candidates.json (후보 메트릭) 저장

주의: 이 스크립트는 "검색이 무엇을 주는가"의 객관 데이터만 만든다.
최종 ✅마땅/△애매/❌안나옴 판정은 사람(코과장)이 after PDF를 눈으로 보고 확정한다.
스크립트가 "됐다"고 판정하지 않는다. (시동 메모 1-C 정직 평가 원칙)
"""
from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import fitz  # PyMuPDF
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from pexels_client import PexelsClient, PexelsPhoto, load_pexels_key  # noqa: E402
from placeholders import PLACEHOLDERS, for_deck  # noqa: E402

PDF_DIR = Path("/Users/hwa/Projects/Automation/TickDeck/v2")
ENV_PATH = "/Users/hwa/Projects/Automation/_env_handoff/WebToSlide/.env"
CACHE = HERE / "cache"
OUT = HERE / "output"

DECK_FILES = {
    "M01": "M01_huchu_automotive_event_demo.pdf",
    "M08": "M08_automotive_brochure_demo.pdf",
    "M12": "M12_huchu_music_demo.pdf",
}


def tone_match_score(photo: PexelsPhoto, want_tone: str) -> float:
    """슬라이드 톤과 사진 톤 일치도 0~1. 다크 슬라이드엔 어두운 사진."""
    luma = photo.luma  # 0~255
    if want_tone == "dark":
        # 어두울수록 높은 점수 (luma 0 -> 1.0, luma 160+ -> 0)
        return max(0.0, 1.0 - luma / 160.0)
    else:  # light
        return max(0.0, min(1.0, (luma - 60) / 160.0))


def aspect_for_orient(orient: str) -> str:
    return {"landscape": "landscape", "portrait": "portrait", "square": "square"}.get(
        orient, "landscape"
    )


def crop_to_box(img_path: str, box_w: float, box_h: float) -> bytes:
    """이미지를 박스 비율에 맞게 center-crop (왜곡 0). 반환 = JPEG bytes."""
    im = Image.open(img_path).convert("RGB")
    iw, ih = im.size
    target = box_w / box_h
    src = iw / ih
    if src > target:
        # 원본이 더 넓음 → 좌우 crop
        new_w = int(ih * target)
        x0 = (iw - new_w) // 2
        im = im.crop((x0, 0, x0 + new_w, ih))
    else:
        new_h = int(iw / target)
        y0 = (ih - new_h) // 2
        im = im.crop((0, y0, iw, y0 + new_h))
    buf = io.BytesIO()
    im.save(buf, format="JPEG", quality=90)
    return buf.getvalue()


def pick_best(client: PexelsClient, ph: dict):
    """검색 → 톤 매칭 정렬 → 최선 + 후보 메트릭 반환."""
    orient = aspect_for_orient(ph["orient"])
    photos, meta = client.search(
        ph["query"], orientation=orient, size="large", per_page=15
    )
    scored = []
    for p in photos:
        # 고화질 필터: 긴 변 2000px 이상만
        if max(p.width, p.height) < 2000:
            continue
        s = tone_match_score(p, ph["tone"])
        scored.append((s, p))
    scored.sort(key=lambda t: -t[0])
    cands = [
        {
            "id": p.id,
            "wh": f"{p.width}x{p.height}",
            "avg_color": p.avg_color,
            "luma": round(p.luma, 1),
            "tone_score": round(s, 3),
            "alt": p.alt[:80],
            "photographer": p.photographer,
            "url": p.url,
        }
        for s, p in scored[:8]
    ]
    best = scored[0][1] if scored else None
    return best, cands, meta


def main():
    key = load_pexels_key(ENV_PATH)
    client = PexelsClient(key)
    spec = {"decks": {}, "method": {}}
    spec["method"] = {
        "keyword_extraction": "슬라이드 헤드라인+본문에서 핵심 명사구 추출 (placeholders.py query)",
        "tone_matching": "슬라이드 톤(dark/light) vs Pexels avg_color 밝기(luma) 매칭 점수 0~1",
        "aspect": "박스 비율에 맞춰 orientation 필터 + center-crop (왜곡 0)",
        "quality": "size=large + 긴 변 2000px 이상만 채택, large2x 다운로드",
        "honest_rule": "pexels_suitable=False(특정 인물/특정 장소)는 검증용으로만 채우고 ❌ 후보로 분류",
    }

    for deck, pdf_name in DECK_FILES.items():
        src_pdf = PDF_DIR / pdf_name
        doc = fitz.open(src_pdf)
        deck_records = []
        for ph in for_deck(deck):
            rec = {
                "slot": ph["slot"], "page": ph["page"], "role": ph["role"],
                "tone": ph["tone"], "orient": ph["orient"],
                "pexels_suitable_apriori": ph["pexels_suitable"],
                "query": ph["query"], "note": ph["note"],
            }
            if ph["role"] == "hero":
                rec["status"] = "EXCLUDED_HERO"  # 후추님 수동 영역
                deck_records.append(rec)
                continue
            if not ph["query"]:
                rec["status"] = "NO_QUERY"
                deck_records.append(rec)
                continue
            best, cands, meta = pick_best(client, ph)
            rec["total_results"] = meta.get("total_results")
            rec["candidates"] = cands
            if best is None:
                rec["status"] = "NO_HIGHRES_RESULT"
                deck_records.append(rec)
                continue
            # 다운로드 + crop + PDF 삽입
            img_path = client.download(best, str(CACHE), prefer="large2x")
            x0, y0, x1, y1 = ph["rect"]
            box_w, box_h = (x1 - x0), (y1 - y0)
            jpeg = crop_to_box(img_path, box_w, box_h)
            page = doc[ph["page"] - 1]
            rect = fitz.Rect(x0, y0, x1, y1)
            page.insert_image(rect, stream=jpeg, keep_proportion=False, overlay=True)
            rec["status"] = "FILLED"
            rec["chosen"] = {
                "id": best.id, "wh": f"{best.width}x{best.height}",
                "avg_color": best.avg_color, "tone_score": round(tone_match_score(best, ph["tone"]), 3),
                "alt": best.alt[:90], "photographer": best.photographer, "url": best.url,
            }
            deck_records.append(rec)
        out_pdf = OUT / f"{deck}_pexels_after.pdf"
        doc.save(out_pdf)
        doc.close()
        spec["decks"][deck] = {"after_pdf": str(out_pdf), "slots": deck_records}
        print(f"[{deck}] saved {out_pdf.name}  slots={len(deck_records)}")

    (OUT / "search_spec.json").write_text(
        json.dumps(spec, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("search_spec.json 저장 완료")


if __name__ == "__main__":
    main()
