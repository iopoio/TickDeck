# python-pptx 전환 계획 — 서버사이드 PPTX 생성

> 현재: 클라이언트(PptxGenJS) → 목표: 서버(python-pptx)
> 임팩트: 디자인 품질 2배 향상 (디자이너 템플릿 활용 가능)

---

## 왜 python-pptx인가

| | PptxGenJS (현재) | python-pptx (목표) |
|---|---|---|
| 실행 위치 | 브라우저 | 서버 |
| 마스터 슬라이드 | ❌ | ✅ 템플릿 .potx 활용 |
| 슬라이드 레이아웃 | 코드로 좌표 찍기 | 플레이스홀더에 데이터 주입 |
| 그라디언트 fill | ❌ | ✅ |
| 그림자 | 복구 오류 | ✅ 정상 |
| 디자이너 협업 | 불가 (코드 = 디자인) | 가능 (PPT 템플릿 = 디자인) |
| 모바일 성능 | 4,500줄 JS 로드 | 서버에서 완성본 전송 |
| PDF 변환 | PPTX 생성 → 서버 전송 → LibreOffice | 서버에서 바로 변환 |

---

## Phase 1: 커버 1장 (3~4시간)

### 목표
커버 슬라이드만 python-pptx로 생성. 나머지 8장은 기존 PptxGenJS 유지.

### 준비물
- PowerPoint 또는 Google Slides에서 **커버 템플릿 .pptx** 생성
  - 플레이스홀더: 회사명, 헤드라인, 서브헤드라인, 로고 위치
  - 디자인: 그라디언트 배경, 그림자, 마스크 등 자유롭게
- `pip install python-pptx` (서버에 이미 Python 환경 있음)

### 구현

```python
# web_to_slide/pptx_builder.py (신규)
from pptx import Presentation
from pptx.util import Inches, Pt

def build_cover_slide(template_path, brand, headline, sub):
    prs = Presentation(template_path)
    slide = prs.slides[0]  # 첫 번째 슬라이드 = 커버 템플릿
    
    # 플레이스홀더에 데이터 주입
    for ph in slide.placeholders:
        if ph.placeholder_format.idx == 0:  # 제목
            ph.text = headline
        elif ph.placeholder_format.idx == 1:  # 부제
            ph.text = sub
    
    # 회사명 텍스트 박스 수정
    # 로고 이미지 삽입
    # 브랜드 컬러 적용
    
    return prs
```

### 통합 방식

```
[파이프라인 완료]
    ↓
[python-pptx] → 커버 1장 PPTX 생성 → /tmp/cover.pptx
    ↓
[PptxGenJS] → 나머지 8장 PPTX 생성 → 브라우저 다운로드
    ↓
[병합?] → 이건 까다로움. 아래 Phase 1.5에서 해결
```

### Phase 1.5: 병합 전략

두 개의 PPTX를 합치는 건 복잡해요. 대안:

**방식 A**: python-pptx가 **전체 9장을 생성**하되, 커버만 템플릿 기반이고 나머지는 코드 생성
→ 이러면 PptxGenJS 코드를 python-pptx로 포팅해야 함 (대규모)

**방식 B**: python-pptx가 커버를 생성 → **PptxGenJS가 나머지를 같은 파일에 추가**
→ PptxGenJS가 기존 PPTX에 슬라이드를 추가하는 기능이 있음 (pptx.write가 아닌 기존 파일 로드)

**방식 C (추천)**: 전체를 python-pptx로 단계적 전환
→ Phase 1에서 커버만, Phase 2에서 CTA+Contact, Phase 3에서 전체

**방식 C로 갑니다.**

### 산출물
- `web_to_slide/pptx_builder.py` — python-pptx 빌더
- `static/templates/cover_a.pptx` — A-type 커버 템플릿
- `/api/generate` 응답에 PPTX 파일 URL 포함

### 검증
- 생성된 커버가 PowerPoint에서 정상 열리는지
- 브랜드 컬러, 회사명, 헤드라인이 정확한지
- 기존 PptxGenJS 결과물과 비교했을 때 품질 향상 체감

---

## Phase 2: CTA + Contact (3~4시간)

### 목표
CTA(8p)와 Contact(9p)도 python-pptx 템플릿으로 전환.

### 추가 템플릿
- `static/templates/cta_a.pptx` — CTA 템플릿 (중앙 정렬 + 카드형)
- `static/templates/contact_a.pptx` — Contact 템플릿 (대형 브랜드 + 2열 연락처)

### 구현
```python
def build_cta_slide(template_path, brand, headline, sub, steps):
    prs = Presentation(template_path)
    slide = prs.slides[0]
    # 헤드라인, 서브, 3-step 카드에 데이터 주입
    return prs

def build_contact_slide(template_path, brand, contact_info):
    prs = Presentation(template_path)
    slide = prs.slides[0]
    # 회사명, 이메일, 전화, 주소 주입
    return prs
```

### 이 시점에서
커버 + CTA + Contact = 3장이 템플릿 기반. 나머지 6장은 PptxGenJS.
**첫인상(커버)과 마지막 인상(CTA+Contact)이 프리미엄** → 체감 효과 큼.

---

## Phase 3: 콘텐츠 슬라이드 전환 (1~2주)

### 목표
나머지 6장(Market Challenge, Pain Analysis, Solution 등)도 python-pptx로 전환.

### 핵심 과제
- 30+ 레이아웃을 python-pptx로 포팅 (대규모)
- 또는: **레이아웃을 5~6개로 통합** (현실적)
  - `split` (텍스트 + 이미지)
  - `cards` (2~4 카드 그리드)
  - `numbered_process` (01, 02, 03 스텝)
  - `stat_3col` (KPI 대형 숫자)
  - `timeline` (수평/수직)

### 템플릿 구조
```
static/templates/
├── cover_a.pptx      # A-type 커버
├── cover_c.pptx      # C-type 커버
├── cover_d.pptx      # D-type 커버
├── cta.pptx          # CTA (공통)
├── contact.pptx      # Contact (공통)
├── split.pptx        # 텍스트+이미지 분할
├── cards_3col.pptx   # 3컬럼 카드
├── cards_2x2.pptx    # 2×2 카드
├── process.pptx      # 번호 프로세스
├── stat.pptx         # KPI 숫자
└── timeline.pptx     # 타임라인
```

### 이 시점에서
PptxGenJS 완전 제거 가능. `static/js/pptmon.js` 삭제.
index.html이 2,355줄 → **~1,500줄**로 더 줄어듦.

---

## Phase 4: 디자이너 협업 구조 (추후)

### 목표
디자이너가 PPT 템플릿을 수정하면 코드 변경 없이 디자인이 바뀌는 구조.

### 워크플로우
```
디자이너 → PowerPoint에서 템플릿 수정 → static/templates/ 업로드
           코드 변경 없음!
```

### 이점
- 디자이너와 개발자의 역할 완전 분리
- A/B 테스트 용이 (템플릿 2개 만들어서 랜덤 적용)
- 고객이 자기 템플릿 업로드 가능 (유료 기능)

---

## 일정 / 담당

| Phase | 작업 | 예상 시간 | 담당 |
|-------|------|----------|------|
| 1 | 커버 템플릿 + python-pptx 빌더 | 3~4시간 | 클과장 설계 + 제대리 구현 |
| 1.5 | PPTX 병합/전체 생성 방식 결정 | 1시간 | 클과장 |
| 2 | CTA + Contact 템플릿 | 3~4시간 | 제대리 |
| 3 | 콘텐츠 슬라이드 전환 | 1~2주 | 제대리 (대규모) |
| 4 | 디자이너 협업 구조 | 추후 | — |

## 리스크

| 리스크 | 대응 |
|--------|------|
| python-pptx가 PptxGenJS보다 기능 부족? | 아니요, 오히려 더 풍부 |
| 서버 부하 증가 | 4GB 서버에서 PPTX 생성은 가벼움 (~1초) |
| 기존 기능 퇴행 | Phase별 점진 전환 + Playwright 테스트 |
| 템플릿 디자인 누가 하나 | 초기는 코드로 생성, 이후 디자이너 or Figma MCP |

---

## 한 줄 결론

> Phase 1 (커버 1장)만 해도 **첫인상이 2배** 좋아져요.
> 그리고 그 과정에서 python-pptx 파이프라인이 갖춰지니까
> Phase 2, 3은 "같은 구조에 템플릿만 추가"하면 돼요.

---

*Planned by Claude Opus 4.6 (클과장)*
