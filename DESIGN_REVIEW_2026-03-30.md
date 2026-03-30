# TickDeck 디자인 리뷰 — 2026-03-30

> 4개 디자인 스킬 기준 전체 리뷰
> - `frontend-design` — 프로덕션급 프론트엔드 미학
> - `make-interfaces-feel-better` — 인터페이스 폴리시 디테일
> - `web-design-guidelines` — Vercel 웹 인터페이스 가이드라인
> - `ui-ux-pro-max` — UI/UX 종합 (접근성, 터치, 타이포, 컬러, 애니메이션)

---

## Part 1: 랜딩 페이지 (landing.html)

### ✅ 잘한 것

**1. 컬러 시스템 — 아주 잘 잡혀 있어요**
- CSS 변수 체계적 (primary/secondary/tertiary + opacity 변형 6단계)
- 3색 팔레트(네이비 #1C3D5A + 세이지 #76B9A1 + 모브 #B98391)가 조화롭고 고급스러움
- 그라디언트 활용이 과하지 않고 자연스러움 (135deg 통일)
- 그림자 컬러도 primary rgba로 통일 → 일관성 ◎

**2. 배경 처리 — 실력 있는 선택**
- 히어로 섹션: 4겹 radial gradient + pseudo-element → 사진 없이도 깊이감
- CTA 섹션: dot pattern 배경 (radial-gradient 2px) → 미묘한 텍스처
- #fbf9f2 웜 크림 배경 → 화이트보다 훨씬 고급스러움

**3. 글래스모피즘 네비게이션**
- `backdrop-filter: blur(24px)` + 70% opacity
- 4% opacity 보더 → 너무 강하지 않아서 좋음
- 이거 꽤 세련된 처리예요 👍

**4. 목업 인터랙션**
- CSS-only 목업 (외부 이미지 없이 구현)
- hover 시 카드 회전 + 이동 (rotate + translate)
- 체크마크 scale 애니메이션 → 성공 피드백 잘 표현

**5. clamp() 반응형 타이포**
- `clamp(40px, 5.5vw, 68px)` — 디바이스별 자연스러운 스케일링
- 이건 정말 좋은 접근이에요

---

### ⚠️ 개선이 필요한 것

#### D1. 동심원 border-radius 미준수 (CRITICAL — make-interfaces-feel-better)

> "Outer radius = inner radius + padding" — 이 규칙이 여러 곳에서 안 지켜지고 있어요.

| 요소 | 외부 radius | 패딩 | 내부 radius | 올바른 내부값 | 상태 |
|------|-----------|------|-----------|------------|------|
| `.hero-mockup` → `.hero-mockup-inner` | 20px | 16px | 12px | 4px | ❌ 내부가 너무 큼 |
| `.hero-mockup` → `.hero-mockup-card` | 20px | ~16px | 10px | 4px | ❌ |
| `.bcta-inner` → `.bcta-btn` | 32px | ~40px | 16px | 독립 OK | ✅ (패딩 24px+ → 독립) |

수정 방향: 내부 요소 radius를 `outerRadius - padding` 으로 맞추거나, 패딩이 24px 이상이면 독립 surface로 처리

#### D2. `transition: all` 사용 (HIGH — make-interfaces-feel-better)

> "Never use `transition: all` — 항상 구체적 속성을 지정"

현재 코드에서 `all` 사용 중:
- `.sc`: `transition: all 0.3s ease` (스텝 카드)
- `.ac`: `transition: all 0.3s ease` (오디언스 카드)
- `.vfi`: `transition: all 0.3s ease` (밸류 피처)
- `.hero-cta`: `transition: all 0.25s ease`
- `.nav-cta`: `transition: all 0.2s ease`

수정: `transition: transform 0.3s ease, box-shadow 0.3s ease` 등으로 구체화

#### D3. 버튼 active 피드백 없음 (MEDIUM — make-interfaces-feel-better)

> "scale(0.96) on press — 항상 0.96 사용"

히어로 CTA, 네비 CTA, 하단 CTA 버튼 모두 hover만 있고 `:active` 스타일이 없어요.

추가 필요:
```css
.hero-cta:active, .nav-cta:active, .bcta-btn:active {
  transform: scale(0.96);
}
```

#### D4. font-smoothing은 있는데 text-wrap 미적용 (LOW — make-interfaces-feel-better)

> "text-wrap: balance on headings, text-wrap: pretty on body"

`-webkit-font-smoothing: antialiased` ✅ 적용됨 (좋아요!)
하지만 `text-wrap: balance` / `text-wrap: pretty` 미적용

추가 필요:
```css
h1, h2, h3, h4 { text-wrap: balance; }
p { text-wrap: pretty; }
```

#### D5. 히트 영역 부족 (MEDIUM — ui-ux-pro-max)

> "최소 44×44px 히트 영역"

- 언어 전환 링크 (🌐 EN): 12px 텍스트, 패딩 미미 → ~20×16px 히트 영역
- 푸터 링크들: 12px, 패딩 없음 → 히트 영역 매우 작음

수정: `padding: 8px 12px` 추가하거나 pseudo-element로 히트 영역 확장

#### D6. 이미지 outline 미적용 (LOW — make-interfaces-feel-better)

> "이미지에 1px outline 추가 → 일관된 깊이감"

커피 QR 이미지에 outline 없음. 추가 필요:
```css
img { outline: 1px solid rgba(0,0,0,0.1); outline-offset: -1px; }
```

#### D7. 폰트 선택 — 좋은데 더 과감해도 됨 (SUGGESTION — frontend-design)

> "Generic 폰트(Inter, Roboto) 대신 distinctive한 선택"

Pretendard + Plus Jakarta Sans는 좋은 선택이에요. 한국어 지원 + 깔끔함.
다만 `frontend-design` 스킬 관점에서 보면, 좀 더 **캐릭터 있는** 조합도 고려해볼 만해요:

- 히어로 h1에만 **Outfit** 또는 **Cabinet Grotesk** 같은 디스플레이 폰트
- 본문은 Pretendard 유지 (한국어 필수)
- 이건 취향 영역이니 참고만 하세요~

#### D8. 모바일 터치 타겟 간격 (MEDIUM — ui-ux-pro-max)

> "터치 타겟 간 최소 8px 간격"

네비게이션에서 `🌐 EN` 링크와 `시작하기` 버튼이 모바일에서 너무 가까울 수 있어요.
`gap: 8px` 이상 확보 필요.

---

### 랜딩 점수

| 기준 | 점수 | 메모 |
|------|------|------|
| 컬러 시스템 | 9/10 | CSS 변수 체계적, 팔레트 조화 |
| 타이포그래피 | 7.5/10 | clamp() 좋음, text-wrap 미적용 |
| 레이아웃 | 8.5/10 | 그리드 잘 잡힘, 반응형 OK |
| 모션/인터랙션 | 6.5/10 | hover 있으나 active 없음, transition: all |
| 표면/깊이감 | 8/10 | 그림자 체계적, 동심원 radius 미준수 |
| 접근성 | 5.5/10 | 히트 영역 부족, ARIA 없음 |
| **종합** | **7.5/10** | |

---

## Part 2: 앱 페이지 (index.html — UI 부분)

### ✅ 잘한 것

**1. 일관된 CSS 변수 시스템**
- `--accent`, `--accent2`, `--success`, `--error` 등 시맨틱 네이밍
- `--radius: 14px` 통일된 radius 변수

**2. 포커스 상태 잘 구현됨**
- Input focus: `box-shadow: 0 0 0 3px rgba(28,61,90,0.12)` + border 변경
- 이건 접근성 면에서 좋은 처리예요 ✅

**3. 진행 표시 디자인**
- 4단계 dot + line 구조 — 단순하면서 명확
- active/done 상태별 색상 구분

### ⚠️ 개선이 필요한 것

#### D9. 버튼 disabled 시 커서만 변경 (MEDIUM — ui-ux-pro-max)

> "loading-buttons: 비활성 + 스피너/프로그레스 표시"

`.btn-primary:disabled`는 `opacity: 0.45` + `cursor: not-allowed`만 있어요.
생성 중일 때 **스피너 아이콘**이나 **로딩 텍스트** 피드백이 더 명확할 수 있어요.

#### D10. 모달 ESC 닫기 (MEDIUM — ui-ux-pro-max)

> "escape-routes: 모달에 cancel/back 제공"

키보드 ESC로 모달 닫기 기능이 있는지 확인 필요.
모달 외부 클릭(backdrop) 닫기도 일관되게 적용되어야 해요.

#### D11. 탭 순서 (LOW — ui-ux-pro-max)

> "keyboard-nav: Tab 순서가 시각적 순서와 일치"

Purpose pill 버튼들, 언어 pill 버튼들의 탭 순서가 시각적 순서와 맞는지 확인 필요.

---

### 앱 페이지 점수

| 기준 | 점수 | 메모 |
|------|------|------|
| 컬러 시스템 | 8.5/10 | 시맨틱 변수, 일관성 |
| 폼/입력 | 8/10 | 포커스 상태 잘 됨 |
| 모달 | 7/10 | 디자인 OK, ESC/키보드 미확인 |
| 진행 표시 | 8/10 | 깔끔한 4단계 |
| 접근성 | 6/10 | ARIA 라벨 부재 |
| **종합** | **7.5/10** | |

---

## Part 3: PPT 슬라이드 디자인 시스템

### ✅ 잘한 것 — 솔직히 이건 진짜 잘 만들었어요

**1. 다이나믹 컬러 시스템 (createColorSystem)**
- 입력: primaryColor + background → 8가지 파생 색상 자동 생성
- HSL 조작으로 accentLight/accentDark 자동 계산
- 라이트/다크 모드 자동 감지 → 텍스트 색상 적응
- **이건 진짜 잘 설계된 시스템이에요** 👏

**2. 30+ 레이아웃 다양성**
- cover, split, cards, portfolio, numbered_process, stat_3col, timeline, radial, comparison_vs, mosaic...
- 각 레이아웃별 고유한 시각 구조
- 연속 동일 레이아웃 자동 방지 로테이션
- 레이아웃 수만으로도 상용 PPT 툴 수준

**3. 아이브로우 필 + 데코 원**
- 모든 슬라이드에 일관된 eyebrow pill (세클 라벨)
- 커버에 대형 원형 데코 (glassmorphism 효과)
- 프로페셔널한 디자인 패턴

**4. 적응형 타이포그래피**
- 텍스트 길이에 따라 폰트 크기 동적 조절
- 한국어/영어 폰트 분리 처리 (Pretendard + NotoSerifKR)
- KPI 숫자 크기가 카드 수에 따라 자동 스케일링

### ⚠️ 개선이 필요한 것

#### D12. 슬라이드 내 타이포 위계 불명확 (HIGH — ui-ux-pro-max)

> "Base 16px, Line-height 1.5, 명확한 타입 스케일"

현재:
- 아이브로우: 9-10px
- 서브헤드: 11-12px
- 바디: 10.5-12.5px ← **서브헤드와 바디가 거의 같은 크기!**

서브헤드라인과 바디 텍스트의 크기 차이가 1-2px밖에 안 돼서 시각적 위계가 약해요.

수정 제안:
```
아이브로우: 8-9px (현재 유지)
헤드라인: 18-24px (현재 유지)
서브헤드: 13-14px (↑ 올리기)
바디: 10-11px (현재 유지)
```

#### D13. 카드 보더 vs 그림자 혼용 (MEDIUM — make-interfaces-feel-better)

> "카드에는 그림자, 구분선에는 보더"

현재 카드 디자인에서:
- `roundedRect` 그리기 → 회색 보더 (rgba(0,0,0,0.08))
- 일부 카드에만 `shadow` 사용

`shadow` 속성은 PPTX 복구 오류를 일으킨다고 이미 기록되어 있어요 (`PM_CARD_SHADOW = undefined`).
이건 PptxGenJS 한계라 어쩔 수 없지만, **보더 두께/색상을 좀 더 미묘하게** 조절하면 좋겠어요:

```javascript
// 현재: 1px solid rgba(0,0,0,0.08)
// 제안: 0.5px solid rgba(0,0,0,0.06) — 더 미묘하게
```

#### D14. KPI 카드 텍스트 대비 (MEDIUM — ui-ux-pro-max)

> "color-contrast: 최소 4.5:1"

KPI 카드에서 accentDark 배경 위에 흰색 텍스트 → OK
하지만 accentLight 배경 위에 흰색 텍스트 → **대비 부족 위험**

`textOnPrimary` 계산에서 밝기 체크는 하고 있지만, accentLight는 별도 체크가 없어요.
accentLight 카드의 텍스트 색상도 밝기 기반 자동 전환이 필요해요.

#### D15. 슬라이드 간 색상 밸런스 (SUGGESTION — frontend-design)

> "Dominant colors with sharp accents outperform timid, evenly-distributed palettes"

현재: primaryColor가 거의 모든 슬라이드에서 동일하게 사용됨
제안: CTA/Contact 슬라이드에서는 primary를 **더 과감하게** (풀 배경),
     콘텐츠 슬라이드에서는 **악센트로만** 사용하는 강약 조절

이건 이미 어느 정도 하고 계시긴 한데, CTA 슬라이드의 "다크 풀배경" 처리가 항상 적용되는 건 아니라서요.

#### D16. 이미지 위 텍스트 가독성 (HIGH — ui-ux-pro-max)

> "color-not-only: 색상만으로 정보 전달 금지"

portfolio/split 레이아웃에서 이미지 위에 흰색 텍스트가 올라갈 때:
- 오버레이 35-40% → **밝은 이미지에서 가독성 부족**
- 특히 흰색 배경 사이트 이미지가 들어오면 텍스트가 안 보일 수 있어요

수정 제안:
- 오버레이 최소 50%로 올리거나
- 텍스트에 `textShadow` 효과 추가 (이미 일부 적용됨, 전체 확대)

---

### PPT 슬라이드 점수

| 기준 | 점수 | 메모 |
|------|------|------|
| 컬러 시스템 | 9/10 | 다이나믹 생성 우수, accentLight 대비 체크 보완 필요 |
| 타이포그래피 | 7/10 | 위계가 sub/body 간 약함 |
| 레이아웃 다양성 | 9.5/10 | 30+ 레이아웃, 자동 로테이션 |
| 표면/카드 | 7.5/10 | PptxGenJS 한계 내 잘 처리, 보더 세밀화 여지 |
| 이미지 처리 | 7/10 | 오버레이 가독성 보완 필요 |
| 전체 일관성 | 8.5/10 | 아이브로우/데코/저작권 바 일관 |
| **종합** | **8/10** | |

---

## 전체 요약 — 우선순위 액션 리스트

### 🔴 꼭 하세요 (HIGH)

| # | 영역 | 이슈 | 예상 작업량 |
|---|------|------|-----------|
| D2 | 랜딩+앱 | `transition: all` → 구체적 속성으로 교체 | 15분 |
| D12 | PPT | 서브헤드/바디 타입 스케일 명확히 | 30분 |
| D16 | PPT | 이미지 오버레이 최소 50% + 텍스트 쉐도우 | 20분 |
| D3 | 랜딩 | 버튼 `:active { scale(0.96) }` 추가 | 5분 |

### 🟡 하면 좋아요 (MEDIUM)

| # | 영역 | 이슈 | 예상 작업량 |
|---|------|------|-----------|
| D1 | 랜딩 | 동심원 border-radius 수정 | 10분 |
| D5 | 랜딩 | 히트 영역 44px 확보 | 10분 |
| D8 | 랜딩 | 모바일 터치 타겟 간격 | 5분 |
| D9 | 앱 | 버튼 로딩 스피너 피드백 | 15분 |
| D13 | PPT | 카드 보더 세밀화 (0.5px, 6% opacity) | 10분 |
| D14 | PPT | accentLight 카드 텍스트 대비 체크 | 15분 |

### 🟢 참고하세요 (LOW/SUGGESTION)

| # | 영역 | 이슈 |
|---|------|------|
| D4 | 랜딩 | `text-wrap: balance/pretty` 적용 |
| D6 | 랜딩 | 이미지 outline 추가 |
| D7 | 랜딩 | 디스플레이 폰트 강화 (선택사항) |
| D10 | 앱 | 모달 ESC 닫기 |
| D11 | 앱 | 탭 순서 검증 |
| D15 | PPT | 슬라이드 간 색상 강약 조절 |

---

## 한 줄 총평

> 전반적으로 **기본기가 탄탄하고 컬러/레이아웃 감각이 좋은** 서비스예요.
> 특히 PPT 다이나믹 컬러 시스템은 진짜 잘 만들었어요 👏
> 다만 **인터랙션 폴리시**(active 피드백, transition 구체화)와
> **접근성 기초**(히트 영역, ARIA)를 보강하면 프로 수준이 될 거예요.

---

*Reviewed by Claude Opus 4.6 — Design Skills Applied:*
*frontend-design · make-interfaces-feel-better · web-design-guidelines · ui-ux-pro-max*
