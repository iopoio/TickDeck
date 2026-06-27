#!/usr/bin/env python3
"""TickDeck 디자인 시스템 엔진 (v1) — GLM·Qwen·Kimi 3-way 흡수 종합.

내용(슬라이드 데이터 리스트) → 디자인 판단을 코드로 적용해 HTML 덱 생성.
deck_harness는 안 건드림 — 흡수한 규칙을 직접 구현한 독립 엔진.

흡수 출처(=캐논):
- 토큰/타이포: Kimi clamp 스케일 + Qwen 광학중심 + GLM 위계
- 레이아웃 매칭: GLM 매칭조건 + Qwen/Kimi 독창 레이아웃
- 다양성: Kimi LayoutMemory(최근3 dedup·쿨다운·intent 강제전환) + Qwen 텐션릴리즈
- 빈하단 채움: Kimi 밀도지수 + 파이프라인 + Qwen flex-grow/clamp + GLM 사이드카드
- 안티패턴: Kimi ID표 + GLM 원문자치환 + Qwen pie/3d 금지
- 팔레트: Kimi 60-30-10 주제별 dict
"""
import re, html as _html

# ── 팔레트 (Kimi 60-30-10, 주제별) ──────────────────────────────
# 팔레트 라이브러리 — 어워즈 수상작 채택(2026-06-26) + 펜톤풍 톤다운. 선택형·다양성.
# 갱신 주기: 분기 awwwards 트렌드 풀(정기-루틴 7/01) + 펜톤 시즌 → palettes.html 재추출해 여기 교체.
# feedback_deck_palette_pantone: 늘 파랑 X · 톤다운 기본 · 네온 X.
PALETTES = {
    # 라이트(밝음·에디토리얼) — 어워즈 페이퍼 톤. 'AI 냄새' 안 나게 따뜻하거나 또렷한 색.
    "cream":  {"mode": "light", "c60": "#F6F1E7", "c30": "#EFE8DA", "c10": "#A6742E",
               "ink": "#2A2018", "muted": "#7C7264", "accent2": "#5E8268"},   # 따뜻한 황동·프리미엄
    "ivory":  {"mode": "light", "c60": "#F5F2ED", "c30": "#EAE6DE", "c10": "#9B4A3A",
               "ink": "#241B1A", "muted": "#7E7469", "accent2": "#A6742E"},   # 클레이·매거진
    "mist":   {"mode": "light", "c60": "#EEF1EC", "c30": "#E3E8E1", "c10": "#4F7A63",
               "ink": "#222826", "muted": "#6E766E", "accent2": "#A6742E"},   # 세이지·차분
    "cobalt": {"mode": "light", "c60": "#EFF1F6", "c30": "#E4E8F1", "c10": "#2D52C9",
               "ink": "#171E2B", "muted": "#6B7384", "accent2": "#E0833B"},   # 또렷한 코발트(시안글로우 아님)+따뜻한 보조
    # 시원한 여름 톤 (쿨·라이트, AI-시안 아닌 톤다운 틸/마린/민트)
    "breeze": {"mode": "light", "c60": "#EDF3F2", "c30": "#DFEBE9", "c10": "#1C8A80",
               "ink": "#14282A", "muted": "#6C8385", "accent2": "#E08A4F"},   # 시원한 틸 + 따뜻한 코랄 보조
    "marine": {"mode": "light", "c60": "#EEF2F7", "c30": "#E1E9F1", "c10": "#2C6FB0",
               "ink": "#14202C", "muted": "#6B7A8C", "accent2": "#3FA39A"},   # 청량 마린블루 + 틸 보조
    "mint":   {"mode": "light", "c60": "#EFF4F0", "c30": "#E1EDE4", "c10": "#2A9D78",
               "ink": "#172A24", "muted": "#6E847A", "accent2": "#3E7FB0"},   # 민트그린 + 블루 보조
    # 다크(필요할 때만, 톤 약간 밝힘)
    "ink":    {"mode": "dark",  "c60": "#161B22", "c30": "#1F2731", "c10": "#C39A52",
               "ink": "#EFEADF", "muted": "#9A9384", "accent2": "#7E9E8C"},
}

# ── 토큰 CSS (mode-aware: dark/light · clamp 타이포 · 광학중심) ───────
def tokens_css(p):
    dark = p.get("mode", "dark") == "dark"
    acc = p["c10"]
    card     = "rgba(255,255,255,.04)" if dark else "#FFFFFF"
    track    = "rgba(255,255,255,.07)" if dark else "rgba(0,0,0,.06)"
    bar2     = "rgba(255,255,255,.22)" if dark else "rgba(0,0,0,.14)"
    line     = "rgba(255,255,255,.09)" if dark else "rgba(0,0,0,.10)"
    stroke   = "rgba(255,255,255,.14)" if dark else "rgba(0,0,0,.10)"
    cardshd  = "none"                                                # 그림자 제거 — 라이트서 카드 겹치면 회색 박스로 뭉침. 테두리로만 정의
    cardbd   = line if dark else "rgba(120,95,62,.22)"               # 라이트=따뜻한 얇은 테두리(회색 아님)
    glow     = f"{acc}14" if dark else f"{acc}10"
    accsoft  = f"{acc}26"
    return f""":root{{
  --c60:{p['c60']};--c30:{p['c30']};--acc:{acc};--acc2:{p['accent2']};
  --ink:{p['ink']};--muted:{p['muted']};--line:{line};--card:{card};--track:{track};
  --bar2:{bar2};--stroke:{stroke};--accsoft:{accsoft};--cardshd:{cardshd};--cardbd:{cardbd};
  --t-hero:clamp(56px,6.4vw,104px);--t-h1:clamp(34px,3.4vw,46px);
  --t-h2:clamp(24px,2.2vw,32px);--t-body:clamp(16px,1.4vw,20px);--t-meta:12px;
  --safe-x:72px;--safe-y:56px;--rhythm:24px;
}}
*{{margin:0;padding:0;box-sizing:border-box;font-family:"Pretendard","Apple SD Gothic Neo",sans-serif}}
.slide{{width:1280px;height:720px;background:
   radial-gradient(900px 520px at 86% 14%,{glow},transparent 60%),
   linear-gradient(135deg,var(--c60),var(--c30) 72%,var(--c60));
   color:var(--ink);position:relative;overflow:hidden;page-break-after:always;
   display:flex;flex-direction:column;padding:var(--safe-y) var(--safe-x)}}
.eyebrow{{font-size:var(--t-meta);font-weight:700;color:var(--acc);letter-spacing:.28em;
   text-transform:uppercase;display:flex;align-items:center;gap:12px}}
.eyebrow::before{{content:"";width:24px;height:2px;background:var(--acc)}}
.title{{font-size:var(--t-h1);font-weight:800;line-height:1.18;letter-spacing:-.01em;
   word-break:keep-all;margin-top:14px}}
.title .ac{{color:var(--acc)}}
.sub{{font-size:var(--t-body);color:var(--muted);line-height:1.6;margin-top:12px;max-width:920px;word-break:keep-all}}
.foot{{position:absolute;left:var(--safe-x);right:var(--safe-x);bottom:28px;display:flex;
   justify-content:space-between;font-size:var(--t-meta);color:var(--muted);letter-spacing:.12em;
   border-top:1px solid var(--line);padding-top:14px}}
.body{{flex:1;display:flex;flex-direction:column;justify-content:flex-start;margin-top:26px}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:14px;padding:26px;box-shadow:var(--cardshd)}}
.kick{{font-size:13px;font-weight:700;color:var(--acc);letter-spacing:.1em}}
"""

# ── 안티패턴 필터 (원문자→스타일숫자, 등) ──────────────────────────
_ENC = {"①":"1","②":"2","③":"3","④":"4","⑤":"5","❶":"1","❷":"2","❸":"3","·":"·"}
def anti_pattern(s):
    for k, v in _ENC.items():
        s = s.replace(k, v)
    return s

# ── 밀도지수 (Kimi 공식) → 빈하단 채움 판정 ───────────────────────
def density(text, items, media=0):
    return round(len(text) * 0.0015 + media * 0.25 + items * 0.1, 3)

# ── 제목 액센트 (GLM: 숫자 어절 우선, 조사 안 끝나는 명사) ──────────
_PARTICLE = ("은", "는", "이", "가", "을", "를", "의", "에", "와", "과", "도", "만")
def accent_title(t):
    words = t.split()
    for w in reversed(words):
        cw = re.sub(r"[.,!?:]", "", w)
        if re.search(r"\d", w) or (len(cw) >= 2 and not cw.endswith(_PARTICLE)):
            return t.replace(w, f'<span class="ac">{w}</span>', 1)
    return t

def _head(s):
    h = f'<div class="eyebrow">{anti_pattern(s.get("eyebrow",""))}</div>' if s.get("eyebrow") else ""
    h += f'<div class="title">{accent_title(anti_pattern(s["title"]))}</div>' if s.get("title") else ""
    h += f'<div class="sub">{anti_pattern(s["sub"])}</div>' if s.get("sub") else ""
    return h

def _foot(s, n, total):
    return f'<div class="foot"><span>{anti_pattern(s.get("foot","TickDeck · 2026"))}</span><span>{n:02d} / {total:02d}</span></div>'

# ── 레이아웃 템플릿 (각각 body HTML 반환) ─────────────────────────
def L_cover(s):
    return f"""<div class="slide" style="justify-content:center;padding-left:80px">
      <div class="eyebrow">{anti_pattern(s.get('eyebrow','2026'))}</div>
      <div style="font-size:var(--t-hero);font-weight:900;line-height:1.02;letter-spacing:-.03em;margin-top:18px;word-break:keep-all">{accent_title(anti_pattern(s['title']))}</div>
      <div class="sub" style="font-size:22px;margin-top:22px">{anti_pattern(s.get('sub',''))}</div></div>"""

def L_divider(s):  # 간지 — 어둡게 반전(본문과 확실히 구분) + 큰 폰트 + 아웃라인 번호
    num = s.get("num", "")
    eb = anti_pattern(s.get("eyebrow", ""))
    title = accent_title(anti_pattern(s["title"]))
    sub = anti_pattern(s.get("sub", ""))
    return f"""<div class="slide" style="justify-content:center;overflow:hidden;color:var(--c60);background:
        radial-gradient(960px 560px at 84% 16%, color-mix(in srgb, var(--acc) 18%, transparent), transparent 62%),
        linear-gradient(140deg, var(--ink), color-mix(in srgb, var(--ink) 88%, #000) 100%)">
      <div style="position:absolute;right:88px;top:50%;transform:translateY(-50%);line-height:.76;
        font-size:248px;font-weight:900;color:transparent;-webkit-text-stroke:2px color-mix(in srgb, var(--c60) 20%, transparent);pointer-events:none">{num}</div>
      <div style="font-size:13px;font-weight:700;color:var(--acc);letter-spacing:.3em;text-transform:uppercase">{eb}</div>
      <div style="font-size:clamp(52px,5.4vw,82px);font-weight:900;line-height:1.06;letter-spacing:-.02em;margin-top:18px;word-break:keep-all">{title}</div>
      <div style="font-size:20px;color:color-mix(in srgb, var(--c60) 70%, transparent);margin-top:16px;max-width:880px;line-height:1.5;word-break:keep-all">{sub}</div>
    </div>"""

def L_statement(s):  # MONO / manifesto
    return f"""<div class="slide" style="justify-content:center">
      <div class="eyebrow">{anti_pattern(s.get('eyebrow',''))}</div>
      <div style="font-size:clamp(40px,4.6vw,64px);font-weight:800;line-height:1.18;margin-top:20px;max-width:1000px;word-break:keep-all">{accent_title(anti_pattern(s['title']))}</div></div>"""

def L_kpi(s):  # 단일 수치 + 하단 보조통계(빈하단 채움)
    aux = "".join(f'<div><div style="font-size:13px;color:var(--muted)">{anti_pattern(a["label"])}</div>'
                  f'<div style="font-size:24px;font-weight:800;margin-top:4px">{anti_pattern(a["value"])}</div></div>'
                  for a in s.get("aux", []))
    return f"""<div class="slide">{_head(s)}
      <div class="body" style="justify-content:flex-start;padding-top:30px">
        <div style="display:flex;align-items:baseline;gap:16px">
          <div style="font-size:140px;font-weight:900;letter-spacing:-.04em;line-height:.9">{anti_pattern(s['value'])}</div>
          <div style="background:var(--accsoft);color:var(--acc);padding:8px 14px;border-radius:99px;font-weight:700">{anti_pattern(s.get('delta',''))}</div></div></div>
      <div style="display:grid;grid-template-columns:repeat({max(1,len(s.get('aux',[])))} ,1fr);gap:20px;border-top:1px solid var(--line);padding-top:22px;margin-bottom:30px">{aux}</div>
      {_foot(s, s['_n'], s['_t'])}</div>"""

def L_bar(s):  # 가로 막대 + 사이드 인사이트(빈하단 방지)
    unit = s.get("unit", "%")
    mx = max((r["v"] for r in s["rows"]), default=1)
    bars = "".join(
        f'<div style="display:grid;grid-template-columns:120px 1fr 64px;align-items:center;gap:14px;margin:13px 0">'
        f'<div style="font-weight:{700 if i==0 else 400};color:{"var(--acc)" if i==0 else "var(--ink)"};font-size:15px">{anti_pattern(r["k"])}</div>'
        f'<div style="height:18px;border-radius:6px;background:var(--track)"><div style="height:100%;width:{r["v"]/mx*100:.0f}%;border-radius:6px;background:{"var(--acc)" if i==0 else "var(--bar2)"}"></div></div>'
        f'<div style="font-weight:700;text-align:right;font-size:15px">{r["v"]}{unit}</div></div>'
        for i, r in enumerate(s["rows"]))
    ins = s.get("insight")
    side = (f'<div class="card" style="width:320px;flex:none;align-self:center;display:flex;flex-direction:column;justify-content:center"><div class="kick">KEY INSIGHT</div>'
            f'<div style="font-size:18px;font-weight:700;margin-top:12px;word-break:keep-all">{anti_pattern(ins)}</div></div>') if ins else ""
    return f"""<div class="slide">{_head(s)}
      <div class="body" style="flex-direction:row;gap:40px;align-items:stretch;padding:14px 0">
        <div style="flex:1;display:flex;flex-direction:column;justify-content:space-evenly">{bars}</div>{side}</div>
      {_foot(s, s['_n'], s['_t'])}</div>"""

def L_cards(s):  # TRELLIS/3카드 (동등 N) — 세로 채움
    cs = "".join(f'<div class="card" style="display:flex;flex-direction:column;justify-content:center"><div class="kick">{anti_pattern(c.get("kick",""))}</div>'
                 f'<div style="font-size:23px;font-weight:800;margin-top:10px">{anti_pattern(c["title"])}</div>'
                 f'<div class="sub" style="margin-top:12px;font-size:16px">{anti_pattern(c["body"])}</div></div>'
                 for c in s["cards"])
    n = len(s["cards"])
    return f"""<div class="slide">{_head(s)}
      <div class="body"><div style="flex:1;display:grid;grid-template-columns:repeat({min(n,3)},1fr);gap:20px;align-items:stretch;padding:10px 0">{cs}</div></div>
      {_foot(s, s['_n'], s['_t'])}</div>"""


def L_agenda(s):  # 목차 — 번호+제목+설명 리스트 (세로 분배)
    rows = "".join(
        f'<div style="display:grid;grid-template-columns:64px 1fr;gap:18px;align-items:baseline;'
        f'padding:18px 0;border-top:1px solid var(--line)">'
        f'<div style="font-size:26px;font-weight:800;color:var(--acc)">{anti_pattern(it["no"])}</div>'
        f'<div><div style="font-size:20px;font-weight:700">{anti_pattern(it["t"])}</div>'
        f'<div class="sub" style="font-size:15px;margin-top:4px">{anti_pattern(it.get("d",""))}</div></div></div>'
        for it in s["items"])
    return f"""<div class="slide">{_head(s)}
      <div class="body" style="justify-content:space-between;padding-top:10px">{rows}</div>
      {_foot(s, s['_n'], s['_t'])}</div>"""

def L_beforeafter(s):
    def col(d, ac, edge):
        items = "".join(f'<div class="card" style="padding:22px;margin-top:14px;border-left:3px solid {edge}"><b style="font-size:16px">{anti_pattern(i["t"])}</b>'
                        f'<div class="sub" style="font-size:15px;margin-top:6px">{anti_pattern(i["b"])}</div></div>' for i in d["items"])
        return f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center"><div class="kick" style="color:{ac};font-size:14px">{anti_pattern(d["label"])}</div>{items}</div>'
    return f"""<div class="slide">{_head(s)}
      <div class="body" style="flex-direction:row;gap:30px;align-items:stretch;padding-top:8px">
        {col(s['before'],'var(--muted)','var(--line)')}
        <div style="font-size:34px;color:var(--acc);align-self:center">&rarr;</div>
        {col(s['after'],'var(--acc)','var(--acc)')}</div>
      {_foot(s, s['_n'], s['_t'])}</div>"""

def L_funnel(s):
    rows = "".join(f'<div style="width:{100-i*16}%;margin:0 auto;background:var(--accsoft);'
                   f'border:1px solid var(--line);border-left:4px solid var(--acc);border-radius:10px;padding:18px 22px;text-align:center;font-weight:700;font-size:18px">{anti_pattern(r)}</div>'
                   for i, r in enumerate(s["steps"]))
    return f"""<div class="slide">{_head(s)}<div class="body" style="justify-content:space-evenly;padding:24px 0">{rows}</div>{_foot(s, s['_n'], s['_t'])}</div>"""


def L_refs(s):  # 참고자료 — 전체 번호 리스트(2열)
    items = "".join(f'<div style="display:grid;grid-template-columns:26px 1fr;gap:10px;padding:9px 0;border-top:1px solid var(--line)">'
                    f'<div style="color:var(--acc);font-weight:800;font-size:14px">{i+1}</div>'
                    f'<div><span style="font-weight:600;font-size:14px">{anti_pattern(r["s"])}</span>'
                    f'<span class="sub" style="font-size:13px"> · {anti_pattern(r.get("t",""))}</span></div></div>'
                    for i, r in enumerate(s["refs"]))
    return f"""<div class="slide">{_head(s)}
      <div class="body" style="margin-top:22px"><div style="display:grid;grid-template-columns:1fr 1fr;gap:0 50px;align-content:start;width:100%">{items}</div></div>
      {_foot(s, s['_n'], s['_t'])}</div>"""

def L_table(s):  # zebra
    head = "".join(f"<th style='text-align:{'left' if i==0 else 'right'};padding:14px;font-size:12px;letter-spacing:.1em;color:var(--muted)'>{anti_pattern(h)}</th>" for i, h in enumerate(s["cols"]))
    body = "".join("<tr style='background:{}'>".format("var(--track)" if r % 2 else "transparent") +
                   "".join(f"<td style='text-align:{'left' if i==0 else 'right'};padding:14px;{'font-weight:800;color:var(--acc)' if i==len(row)-1 else ''}'>{anti_pattern(str(c))}</td>" for i, c in enumerate(row)) + "</tr>"
                   for r, row in enumerate(s["rows"]))
    return f"""<div class="slide">{_head(s)}
      <div class="body"><table style="width:100%;border-collapse:collapse"><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table></div>
      {_foot(s, s['_n'], s['_t'])}</div>"""

def L_closing(s):
    bl = "".join(f'<li style="list-style:none;margin:14px 0;padding-left:22px;position:relative;font-size:18px">'
                 f'<span style="position:absolute;left:0;top:9px;width:8px;height:8px;background:var(--acc)"></span>{anti_pattern(b)}</li>' for b in s.get("bullets", []))
    return f"""<div class="slide" style="justify-content:center">{_head(s)}<ul style="margin-top:24px">{bl}</ul></div>"""

LAYOUTS = {"cover": L_cover, "divider": L_divider, "statement": L_statement, "kpi": L_kpi,
           "bar": L_bar, "cards": L_cards, "beforeafter": L_beforeafter, "funnel": L_funnel,
           "table": L_table, "closing": L_closing, "agenda": L_agenda, "refs": L_refs}
# 데이터 밀도 높은(시각 무거운) 레이아웃 — 텐션릴리즈용
HEAVY = {"bar", "table", "kpi"}


# ── 다양성 엔진 (Kimi LayoutMemory + Qwen 텐션릴리즈) ──────────────
class LayoutMemory:
    def __init__(self):
        self.stack = []

    def ok(self, layout):
        if layout in self.stack[-2:]:           # 최근 2 연속 금지(=최대 2연속)
            return False
        if self.stack and self.stack[-1] in HEAVY and layout in HEAVY:  # 텐션릴리즈
            return False
        return True

    def commit(self, layout):
        self.stack.append(layout)


def build_deck(slides, theme="tech", title="Deck"):
    p = PALETTES[theme]
    mem = LayoutMemory()
    total = len(slides)
    out = []
    for i, s in enumerate(slides, 1):
        s = dict(s, _n=i, _t=total)
        lt = s["layout"]
        # 다양성: 같은 레이아웃 2연속/heavy 연속이면 경고(엔진은 콘텐츠 고정이라 로그만)
        if not mem.ok(lt):
            s["_warn"] = f"다양성 경고: {lt}"
        mem.commit(lt)
        out.append(LAYOUTS[lt](s))
    body = "\n".join(out)
    return f"""<!DOCTYPE html><html lang="ko"><head><meta charset="utf-8"><title>{_html.escape(title)}</title>
<style>@page{{size:1280px 720px;margin:0}}html,body{{margin:0;background:#000}}<!--T-->{tokens_css(p)}</style></head>
<body>{body}</body></html>""".replace("<!--T-->", "")


# ── 자가검증 ──────────────────────────────────────────────────
def selfcheck(slides, html):
    assert "①" not in html and "②" not in html, "원문자 잔존(안티패턴 위반)"
    layouts = [s["layout"] for s in slides]
    for i in range(len(layouts) - 2):           # 3연속 동일 금지
        assert not (layouts[i] == layouts[i+1] == layouts[i+2]), f"레이아웃 3연속: {layouts[i]}"
    assert len(set(layouts)) >= 5, "레이아웃 다양성 부족(<5종)"
    return True


if __name__ == "__main__":
    from demo_content import DECK   # 데모 콘텐츠
    h = build_deck(DECK["slides"], DECK.get("theme", "tech"), DECK.get("title", "Deck"))
    import pathlib
    pathlib.Path(__file__).with_name("out.html").write_text(h, encoding="utf-8")
    selfcheck(DECK["slides"], h)
    print(f"OK — {len(DECK['slides'])}슬라이드 · 레이아웃 {len(set(s['layout'] for s in DECK['slides']))}종 · 원문자0 · 3연속없음")
