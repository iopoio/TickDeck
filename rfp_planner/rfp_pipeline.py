#!/usr/bin/env python3
"""RFP → 배점-매칭 제안 골격 파이프라인 (TickDeck 수주-제안 vertical).

공공 RFP(나라장터 .hwp/.hwpx) 한 건을 넣으면:
  공고번호 → 첨부 제안요청서 다운로드 → 표 포함 텍스트 추출 → 평가배점표 파싱
  → 배점 비중대로 분량 배분한 '제안 골격(skeleton.json)' 생성.

deck_harness/v3(레이아웃 렌더)는 건드리지 않는다. 이건 그 앞단 얇은 층 =
"RFP를 읽어 무엇을 어느 비중으로 쓸지"를 결정하는 0순위 골격 생성기.

검증된 사실(2026-06-27 본부 정찰):
  - 나라장터 입찰공고: GET .../1230000/ad/BidPublicInfoService/getBidPblancListInfoServcPPSSrch
  - 첨부 URL = 공고 레코드의 ntceSpecDocUrl1..N
  - .hwp(바이너리) 표 추출 = hwp5html (Think/.venv) → xhtml <td>
  - data.go.kr 키 = pepstocks/.env.local 의 DATAGOKR_API_KEY

ponytail: 배점표가 '항목명(NN)' 형태로 박힌 RFP에 맞춤. 별도 배점 칼럼만 있는
양식은 parse_scoring 확장 필요(backlog #2 후속). 동작 fixture = KOREA360 USA.
"""
from __future__ import annotations
import re, json, html, shutil, zipfile, tempfile, subprocess, urllib.parse, urllib.request, ssl
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]            # .../Automation
HWP5HTML = ROOT / "Think/.venv/bin/hwp5html"
ENV_KEY  = ROOT / "pepstocks/.env.local"
API = "http://apis.data.go.kr/1230000/ad/BidPublicInfoService"
_CTX = ssl.create_default_context(); _CTX.check_hostname = False; _CTX.verify_mode = ssl.CERT_NONE
_UA = {"User-Agent": "Mozilla/5.0"}

# 전형적 배점 단위(오탐 차단용). 다른 RFP가 7/13 같은 배점이면 여기 넓힌다.
_PLAUSIBLE = {5,7,8,10,12,15,20,25,30,35,40,45,50,60,70,80,90,100}


def load_key() -> str:
    for line in ENV_KEY.read_text().splitlines():
        if line.startswith("DATAGOKR_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"DATAGOKR_API_KEY 없음: {ENV_KEY}")


def _api(op: str, params: dict) -> dict:
    url = f"{API}/{op}?{urllib.parse.urlencode({**params, 'serviceKey': load_key()}, safe='')}"
    with urllib.request.urlopen(url, timeout=40, context=_CTX) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def find_notice(bid_no: str, keyword: str, bgn: str, end: str) -> dict:
    """공고번호로 공고 레코드(첨부 URL 포함) 회수. keyword = 검색 좁히기용."""
    j = _api("getBidPblancListInfoServcPPSSrch",
             {"pageNo": 1, "numOfRows": 100, "type": "json", "inqryDiv": 1,
              "inqryBgnDt": bgn, "inqryEndDt": end, "bidNtceNm": keyword})
    items = j["response"]["body"].get("items") or []
    if isinstance(items, dict):
        items = items.get("item", [])
    rec = next((it for it in items if it.get("bidNtceNo") == bid_no), None)
    if not rec:
        raise SystemExit(f"공고 {bid_no} 못 찾음(키워드 '{keyword}' 범위 {bgn}~{end}).")
    return rec


def attachments(rec: dict) -> list[tuple[str, str]]:
    out = []
    for i in range(1, 11):
        fn, u = rec.get(f"ntceSpecFileNm{i}"), rec.get(f"ntceSpecDocUrl{i}")
        if fn and u:
            out.append((fn, u))
    return out


def pick_rfp(atts: list[tuple[str, str]]) -> tuple[str, str]:
    """제안요청서 우선, 없으면 첫 hwp/hwpx."""
    for fn, u in atts:
        if "제안" in fn or "과업" in fn:
            return fn, u
    for fn, u in atts:
        if fn.lower().endswith((".hwp", ".hwpx")):
            return fn, u
    raise SystemExit("hwp 첨부 없음.")


def download(url: str, dest: Path) -> Path:
    with urllib.request.urlopen(urllib.request.Request(url, headers=_UA), timeout=60, context=_CTX) as r:
        dest.write_bytes(r.read())
    return dest


def extract(path: Path) -> tuple[str, list[str]]:
    """RFP 파일 → (본문텍스트, 표셀리스트). .hwp=hwp5html, .hwpx=zip."""
    if path.suffix.lower() == ".hwpx":
        blob = ""
        z = zipfile.ZipFile(path)
        for n in z.namelist():
            if re.search(r"Contents/section\d+\.xml", n):
                blob += z.read(n).decode("utf-8", "replace")
        cells = [re.sub(r"<[^>]+>", "", c).strip()
                 for c in re.findall(r"<hp:tc.*?>(.*?)</hp:tc>", blob, re.S)]
        text = re.sub(r"<[^>]+>", "", re.sub(r"</hp:p>", "\n", blob))
        return text, cells
    # .hwp (바이너리) → hwp5html
    out = Path(tempfile.mkdtemp())
    subprocess.run([str(HWP5HTML), "--output", str(out), str(path)], check=True,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    blob = "".join(fp.read_text("utf-8", "replace") for fp in out.rglob("*.xhtml"))
    shutil.rmtree(out, ignore_errors=True)
    cells = [re.sub(r"<[^>]+>", "", html.unescape(c)).strip().replace("\n", " ")
             for c in re.findall(r"<td[^>]*>(.*?)</td>", blob, re.S)]
    text = re.sub(r"<[^>]+>", " ", html.unescape(blob))
    return text, [c for c in cells if c]


_LABEL_KW = "이해|역량|수행|관리|적정|우수|계획|전문|타당|추진|실현|구체|창의|품질|방안|체계|전략|기술|가격"


def _is_label(c: str) -> bool:
    """평가요소 항목명처럼 보이는 셀(짧고, 번호매김 또는 평가 키워드, 설명문 ㅇ/- 아님)."""
    if c.startswith(("ㅇ", "-", "∘", "·", "※")) or not (2 <= len(c) <= 30):
        return False
    return bool(re.match(r"^\s*\d+\s*[\).]", c) or re.search(_LABEL_KW, c))


def parse_scoring(cells: list[str]) -> dict:
    """평가배점표 → 기술항목/가격 분리. (backlog #1~#3)
    (a) 인라인 '항목(NN[점])' = 전체 셀(패턴이 특정적이라 구간 불필요)
    (b) 칼럼형 '[요소]...[NN]' = '평가항목/요소' 헤더~'합계' 구간 안에서만(숫자 오탐 차단)"""
    pairs, seen = [], set()

    def add(name, pts):
        name = re.sub(r"^\s*\d+\s*[\).]\s*", "", re.sub(r"\s+", " ", name)).strip()
        if pts in _PLAUSIBLE and name and (name, pts) not in seen:
            seen.add((name, pts)); pairs.append({"항목": name, "배점": pts})

    # (a) 인라인
    for c in cells:
        m = re.fullmatch(r"\s*([가-힣][가-힣A-Za-z·\s]{1,18})\((\d{1,3})\s*점?\)\s*", c)
        if m:
            add(m.group(1), int(m.group(2)))
    # (b) 칼럼형 — 짧은 헤더 셀로 구간 시작, 합계/별지 짧은 셀에서 종료
    start = next((i for i, c in enumerate(cells) if re.fullmatch(r"\s*평가\s*(항목|요소)\s*", c)), None)
    if start is not None:
        last = None
        for c in cells[start + 1:]:
            if re.fullmatch(r"\s*(합\s*계|총\s*계|소\s*계)\s*", c) or (len(c) <= 18 and re.search(r"별지|별첨|서식", c)):
                break
            if _is_label(c):
                last = c
            elif re.fullmatch(r"\d{1,3}", c) and last:
                add(last, int(c)); last = None

    price = next((p for p in pairs if "가격" in p["항목"]), None)
    tech = [p for p in pairs if "가격" not in p["항목"]]
    # 소계 제거: 이름에 '평가' 포함 & 배점이 나머지 기술항목 합과 같음(예: 기술능력평가(80))
    tech = [p for p in tech
            if not ("평가" in p["항목"] and p["배점"] == sum(q["배점"] for q in tech if q is not p))]
    return {"기술항목": tech, "기술합": sum(p["배점"] for p in tech), "가격": price}


def extract_constraints(text: str) -> list[str]:
    """제안 작성에 박아넣어야 할 RFP 제약. (backlog #4)"""
    c = []
    if "모호한 표현" in text or re.search(r"~?할 수 있다", text):
        c.append("모호어 금지 — '~할 수 있다/가능하다'류는 불가능으로 간주됨. 단정형으로.")
    if "원본 1부" in text:
        c.append("제출 = 원본 1부 + 업체정보 삭제본 1부")
    if "발표평가" in text or "발표 평가" in text:
        c.append("발표평가 포함 — 발표용 구성 필요")
    m = re.search(r"(\d{1,3})\s*(?:페이지|쪽|매)\s*(?:이내|이하)", text)
    if m:
        c.append(f"제안서 분량 제한 {m.group(1)}쪽 이내")
    return c


def build_skeleton(scoring: dict, constraints: list[str], total_slides: int = 12) -> dict:
    """평가항목 → 배점 비중대로 슬라이드 분량 배분한 제안 골격. (backlog #3)"""
    tech, ttot = scoring["기술항목"], scoring["기술합"] or 1
    sections = []
    for it in sorted(tech, key=lambda x: -x["배점"]):
        n = max(1, round(it["배점"] / ttot * total_slides))
        sections.append({"평가항목": it["항목"], "노리는배점": it["배점"], "슬라이드수": n,
                         "지시": f"이 섹션은 평가위원이 '{it['항목']}'({it['배점']}점)를 채점하는 곳. "
                                 f"배점이 클수록 깊게."})
    return {"기술배점합": scoring["기술합"], "가격배점": (scoring["가격"] or {}).get("배점"),
            "총슬라이드(기술)": sum(s["슬라이드수"] for s in sections),
            "섹션": sections, "RFP제약": constraints}


def run_from_file(path: Path, total_slides: int = 12) -> dict:
    text, cells = extract(path)
    scoring = parse_scoring(cells)
    return build_skeleton(scoring, extract_constraints(text), total_slides)


def run_from_notice(bid_no: str, keyword: str, bgn: str, end: str, workdir: Path) -> dict:
    rec = find_notice(bid_no, keyword, bgn, end)
    fn, url = pick_rfp(attachments(rec))
    workdir.mkdir(parents=True, exist_ok=True)
    f = download(url, workdir / fn)
    sk = run_from_file(f)
    sk["공고"] = {"공고명": rec.get("bidNtceNm"), "발주": rec.get("ntceInsttNm"),
                 "추정가": rec.get("presmptPrce"), "개찰": rec.get("opengDt"), "RFP파일": fn}
    return sk


def _report(sk: dict) -> str:
    L = []
    if "공고" in sk:
        g = sk["공고"]; L.append(f"# {g['공고명']}\n발주 {g['발주']} | 추정가 {g['추정가']} | 개찰 {g['개찰']}")
    L.append(f"\n기술 {sk['기술배점합']}점 + 가격 {sk['가격배점']}점 | 제안 골격 {sk['총슬라이드(기술)']}슬라이드")
    for s in sk["섹션"]:
        L.append(f"  · [{s['노리는배점']:>2}점] {s['평가항목']:<14} → {s['슬라이드수']}슬라이드")
    if sk["RFP제약"]:
        L.append("\n제약(카피에 주입):")
        L += [f"  - {c}" for c in sk["RFP제약"]]
    return "\n".join(L)


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("target", help="나라장터 공고번호(R26...) 또는 로컬 RFP 파일 경로")
    ap.add_argument("--keyword", default="홍보", help="공고 검색 좁히기 키워드")
    ap.add_argument("--bgn", default="202606200000"); ap.add_argument("--end", default="202606272359")
    ap.add_argument("--out", default=None, help="skeleton.json 저장 경로")
    a = ap.parse_args()
    p = Path(a.target)
    if p.exists():
        sk = run_from_file(p)
    else:
        sk = run_from_notice(a.target, a.keyword, a.bgn, a.end, Path(__file__).parent / "_work")
    print(_report(sk))
    out = Path(a.out) if a.out else Path(__file__).parent / "_work" / "skeleton.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(sk, ensure_ascii=False, indent=2))
    print(f"\n→ {out}")
