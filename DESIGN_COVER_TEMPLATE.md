# 커버 템플릿 설계서 — python-pptx Phase 1

> 클과장 설계 / 제대리 구현 참고용

---

## 1. 커버 디자인 스펙

### 슬라이드 사이즈
- 16:9 와이드 (13.333" × 7.5")
- 기존 PptxGenJS와 동일

### 레이아웃 구조

```
┌──────────────────────────────────────────────┐
│                                              │
│  ┌─────────────┐                             │
│  │ COMPANY NAME │  ← pill badge (primary)    │
│  └─────────────┘                             │
│                                              │
│                                              │
│  헤드라인을 여기에                          ○ │ ← 데코 원 1개
│  크고 과감하게                               │    (primary, 투명도 88%)
│                                              │
│  ──────                                      │
│  서브헤드라인 (tintedGray)                   │
│                                              │
│                                    [로고]    │
│ © 2026 Company                        1 / 9  │
│██████████████████████████████████████████████│ ← 하단 bar (primary)
└──────────────────────────────────────────────┘
```

### 요소별 상세 스펙

| 요소 | 위치 | 크기 | 색상 | 폰트 |
|------|------|------|------|------|
| pill badge | x:10%, y:16% | 동적 (텍스트 기반) | primary fill, white text | Pretendard Bold 9pt, 자간 2pt |
| 헤드라인 | x:10%, y:26% | w:72%, h:42% | white | Pretendard Bold 52~80pt (길이별 동적) |
| accent line | x:10%, y:70% | w:10%, h:3pt | primary | — |
| 서브헤드라인 | x:10%, y:74% | w:72%, h:12% | tintedGray | Pretendard Regular 18pt |
| 로고 | x: 우하단 | max 1.8"×0.5" | 원본 | — |
| 저작권 | x:좌하단 | — | tintedGray 7pt | Pretendard |
| 페이지번호 | x:우하단 | — | white 9pt | Pretendard |
| 데코 원 | x:60%, y:-10% | 지름 H×1.1 | primary, 투명도 88% | — |
| 하단 bar | x:0, y:100%-6% | 전폭, h:6% | primary | — |
| 배경 | 전체 | — | tintedDark | — |

---

## 2. 동적 컬러 시스템

python-pptx에서 브랜드 컬러를 받아서 동적으로 적용:

```python
def _tinted_dark(primary_hex):
    """primary hue를 섞은 거의-검정 (커버 배경)"""
    # HSL로 변환 → L을 0.08로, S를 0.25로 → 다시 RGB
    # 결과: 순수 검정이 아닌 primary 색조가 묻은 어두운 색

def _tinted_gray(primary_hex):
    """primary hue를 섞은 중간 회색 (서브텍스트)"""
    # HSL → L을 0.55로, S를 0.08로

def _apply_brand_colors(slide, primary_hex):
    """슬라이드의 모든 요소에 브랜드 컬러 적용"""
    bg_color = _tinted_dark(primary_hex)
    gray_color = _tinted_gray(primary_hex)
    # 배경, pill, accent line, 하단 bar, 데코 원에 primary 적용
    # 서브텍스트, 저작권에 tintedGray 적용
```

### 컬러 매핑

| 요소 | 컬러 소스 |
|------|----------|
| 배경 | tintedDark(primary) |
| pill badge 배경 | primary |
| pill badge 텍스트 | white (또는 textOnPrimary) |
| 헤드라인 | white |
| 서브헤드라인 | tintedGray(primary) |
| accent line | primary |
| 데코 원 | primary + 투명도 88% |
| 하단 bar | primary |
| 저작권/페이지번호 | tintedGray(primary) |

---

## 3. 헤드라인 동적 사이징

```python
def _headline_font_size(text):
    length = len(text)
    if length > 28:
        return Pt(52)
    elif length > 18:
        return Pt(64)
    else:
        return Pt(80)
```

---

## 4. Narrative Type별 변형

### A-type (Tech/SaaS) — 기본
- 위 설계 그대로

### B-type (제조/인프라)
- 상단에 institutional band (primary, h:6%)
- 로고 우상단으로 이동

### C-type (크리에이티브)
- 이미지 있으면: 풀블리드 이미지 + 다크 오버레이 + 좌측 텍스트
- 이미지 없으면: 다크 배경 + 좌 primary bar + 대형 데코 원

### D-type (럭셔리/B2C)
- 극세선 테두리 (상하 3pt primary)
- 헤드라인 non-bold, 자간 넓게
- 여백 극대화

### F-type (교육/전문서비스)
- 밝은 배경 (#FAFAFA)
- 좌 primary bar + 상단 accentLight 선
- 텍스트 어두운 색

---

## 5. 템플릿 생성 방식

두 가지 선택지:

### 방식 A: PowerPoint에서 수동 제작
- 디자이너가 PPT에서 직접 디자인
- 플레이스홀더 배치
- python-pptx가 플레이스홀더에 데이터 주입만

**장점**: 디자인 자유도 최고
**단점**: 타입별로 5개 파일 만들어야 함, 색상 동적 변경 어려움

### 방식 B: python-pptx 코드로 생성 (추천)
- 코드에서 슬라이드 처음부터 빌드
- 그라디언트, 그림자 등 PptxGenJS에서 못 했던 기능 활용
- 브랜드 컬러 동적 적용 자유로움

**장점**: 컬러 동적 변경 완벽, 1개 함수로 5개 타입 커버
**단점**: 코드가 디자인 (하지만 지금도 그래요)

**→ Phase 1은 방식 B로. Phase 4에서 방식 A 도입.**

---

## 6. PptxGenJS에서 못 했던 것 — python-pptx에서 할 것

### 그라디언트 배경
```python
from pptx.oxml.ns import qn
# 2색 선형 그라디언트 (tintedDark → primary 10%)
background = slide.background
fill = background.fill
fill.gradient()
fill.gradient_stops[0].color.rgb = RGBColor(0x0A, 0x0C, 0x14)  # tintedDark
fill.gradient_stops[1].color.rgb = RGBColor(0x1C, 0x3D, 0x5A)  # primary 10%
```

### 도형 그림자
```python
from pptx.oxml.ns import qn
# PptxGenJS에서는 복구 오류 → python-pptx에서는 정상
shape = slide.shapes.add_shape(...)
shadow = shape.shadow
shadow.inherit = False
shadow.blur_radius = Pt(12)
shadow.distance = Pt(4)
shadow.angle = 90
```

### 투명도 있는 fill
```python
# PptxGenJS transparency는 제한적 → python-pptx는 alpha 직접 제어
from pptx.oxml.ns import qn
fill_elem = shape._element.spPr.solidFill
fill_elem.srgbClr.attrib[qn('a:alpha')] = '12000'  # 12% 불투명 = 88% 투명
```

---

## 7. 파일 구조

```
web_to_slide/
├── pptx_builder.py       ← 신규: python-pptx 빌더
│   ├── build_cover()     ← 커버 슬라이드 생성
│   ├── _tinted_dark()    ← 틴티드 컬러 유틸
│   ├── _tinted_gray()
│   └── _headline_fs()    ← 동적 사이징

app.py
├── POST /api/preview-cover  ← 신규: 커버 미리보기 API
```

---

## 8. 성공 기준

1. PowerPoint에서 열었을 때 **복구 오류 0**
2. 그라디언트 배경이 보이는지
3. 데코 원에 **투명도**가 제대로 적용되는지
4. 브랜드 컬러 바꿨을 때 **전체 톤이 통일**되는지
5. 기존 PptxGenJS 커버와 비교했을 때 **"확실히 낫다"** 체감

---

*Designed by Claude Opus 4.6 (클과장)*
