# Design Decomposition — Deloitte Digital "Five Trends Shaping Marketing in 2026"

- Source PDF: `/Users/hwa/Downloads/2026 marketing/deloitte-nl-deloitte-digital-marketing-trends-2026.pdf`
- 18 pages, landscape 16:9. Rendered + sampled pages: 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 15 (cover / statement dividers / data intro / section divider / 4-col body / card grid / big-number stat / process matrix / trends index / trend-body archetype).
- Purpose: extract reusable layout/typography/spacing **discipline** for the TickDeck deck engine. Brand-only skins are tagged `[브랜드전용·복제금지]`.

---

## PART A — DESIGN DECOMPOSITION

### 1. Overall System (grid, whitespace, rhythm, light/dark)

- **Canvas**: 16:9 landscape. Generous, consistent outer margin (~6–7% on all sides). Content never touches the edge; the margin is the frame.
- **Two macro-layouts alternate to create rhythm**:
  - **DARK "statement" pages** (p2, p4, p6) — full-bleed abstract gradient image, large headline lower-left, almost no body. These act as palate-cleansers / chapter breaks. Roughly 1 dark page precedes every 2–4 light content pages.
  - **LIGHT "work" pages** (p3, p5, p7, p8, p9, p10, p11, p12–16) — near-white background, structured multi-column or card grids.
- **Grid discipline on light pages**: a clear N-column system, N ∈ {2, 3, 4, 5}, driven by the *count of the idea* (4 consumer shifts → 4 cols p5; 5 AI truths → 5 cols p7; 5 trends → 5 rows p11). The number of items dictates the grid; columns are equal-width with even gutters.
- **Title band**: every light content page opens with a single-line H1 anchored top-left on its own horizontal band, a thin rule or whitespace gap below it, then the grid. Page title sits in the SAME position on every page → strong vertical rhythm when flipping.
- **Whitespace ratio**: high. On 4–5 column pages each cell is mostly air around a small icon + short text block; text fills maybe 40–50% of each column. Pages never look packed even when dense (p8 process matrix is the one deliberate exception).
- **Footer**: persistent, tiny, bottom — `N | Deloitte Digital Marketing Trends 2026` bottom-left, source line bottom-right where relevant. Same baseline on every page.

### 2. Color

- **Base (light pages)**: warm off-white / very light cool-grey background, NOT pure white (≈ `#F4F4F2`/`#F2F3F4`). Soft. Reduces glare vs stark white.
- **Primary text / headlines**: Deloitte deep green-black for H1 on light pages (≈ `#046A38` true green used for the BIG headline color, e.g. cover title and big numbers; body text in near-black `#1A1A1A`). `[브랜드전용·복제금지: 딥 그린 #046A38 = Deloitte 정체성색. 규율만 차용 — "헤드라인·빅넘버에 단일 브랜드 채도색 1개" 패턴은 가져오되 hex는 우리 브랜드색으로 교체]`
- **Accent**: a single saturated green carries headlines + statistics + icon strokes. The deck is essentially **monochrome-accent**: one brand hue + ink + paper, nothing competing.
- **Dark statement pages**: full-bleed liquid/ink swirl gradients (teal → magenta → orange → cobalt) on dark ground; headline reversed to white with one keyword sometimes in accent. `[브랜드전용·복제금지: 특정 swirl 3D 렌더 = 자산. 규율만 — "간지 페이지 = 풀블리드 추상 이미지 + 반전 흰 헤드라인"]`
- **Color encodes meaning**:
  - Accent green = "this is the number that matters" (all big stats are green).
  - On the p3 two-column table, **left col = OBSERVATION, right col = IMPACT**, separated purely by position + an icon column, no color blocks needed.
  - Tone is **restrained / corporate-confident**, never vivid except inside the contained gradient art. Body palette is almost austere; vividness is rationed to the divider images only.

### 3. Typography

- **Single sans-serif family** across the whole deck (humanist sans, Deloitte's brand face / similar to a clean grotesque). **No serif anywhere.** `[브랜드전용·복제금지: 정확한 브랜드 폰트. 규율 — "전 덱 단일 산세리프 1종"]`
- **Hierarchy (relative scale, approx):**
  - **Display / divider headline** (p2, p4 etc.): ~40–54pt, light-to-regular weight, can wrap 2 lines. Mixes weights inside one headline — e.g. p2 "**Marketing** as we know **it is over.**" sets emphasis words bold and connective words light in the SAME line.
  - **H1 page title**: ~24–28pt, light/regular weight, sentence case, single line.
  - **Card/column heading**: ~13–15pt, semibold, often Title Case or sentence case, 1–2 lines.
  - **Body**: ~9–10pt, regular, generous line-height (~1.4), short paragraphs (2–4 lines).
  - **Caption / source / footer**: ~7–8pt, grey, regular.
  - **BIG NUMBER stat**: ~48–72pt, the largest type on any work page, accent green, paired with a 2-line grey explainer beneath.
- **Headline treatment**: lowercase-leaning sentence case, weight-mixing for emphasis instead of color or size jumps. Calm.
- **Number / stat styling**: oversized, accent-colored, set as the visual hero of its cell; the explanatory sentence is deliberately small and grey so the eye lands on the figure first. Percent sign kept same weight as digits.

### 4. Layout Archetypes (text-layout maps)

- **COVER (p1)** — left/right split. LEFT ~55%: H1 title (2 lines, accent green) top-third, one-line subhead below, date below that, brand lockup bottom-left. RIGHT ~45%: single hero object (3D swirl sphere) floating on paper, vertically centered. No box, no rule — whitespace does the dividing.
- **STATEMENT / DIVIDER (p2, p4, p6)** — full-bleed dark gradient image. Headline anchored **lower-left** (p2) or **mid-left** (p6), reversed white, 2–3 lines. Optional tiny dek line under it. Icons/nav cluster top-right. Almost zero body copy. p4 variant overlays an editorial collage but keeps the big reversed left-anchored label ("CUSTOMERS ARE CHANGING").
- **TWO-COLUMN COMPARE (p3)** — H1 across top. Below, a repeating row pattern: `[icon] OBSERVATION text  ||  [icon] IMPACT text`. Left and right are two labeled lanes; ~5 rows stacked. The compare is positional, not boxed.
- **N-COLUMN CONCEPT GRID (p5 = 4 col, p7 = 5 col)** — H1 + one-line dek across top. Then equal columns, each: small line-icon at top → short bold heading → 2–4 line body. p5 then drops a **stat band along the bottom** (big green % per column) tying a figure to each concept. p7 adds a row of small photo thumbnails under the 5 cards as texture.
- **PROCESS / DATA MATRIX (p8)** — densest page. H1 top. A horizontal swimlane table: rows = phases of the marketing lifecycle, columns = stages; cells are small pill-labels. A row of **5 big green stat callouts** (+48%, 100X, 300X, +50%, +36%) sits above the matrix as the headline takeaways. Source line bottom.
- **BIG-NUMBER STAT ROW (p9)** — H1 top, source directly under it. Then 4 evenly spaced cells each: line-icon → **huge green stat** → 2-line grey explainer. Pure "wall of proof" layout.
- **INDEX / AGENDA (p11)** — left ~30% column holds the section title ("5 Marketing trends…") + intro paragraph. Right ~70% is a vertical numbered list: `01` large outline numeral | ALL-CAPS trend title | one-line description. Five stacked rows = the deck's table of contents.
- **TREND BODY ARCHETYPE (p12–16, identical template ×5)** — the workhorse. Layout map:
  - Top-left: numbered H1 ("1. AI becomes the Operating System of Marketing").
  - Upper-left block: **WHAT WE SEE** label + 2–3 line paragraph.
  - Lower-left block: **PRIMARY DRIVERS** label + numbered `01/02/03` list, each a bold lead-in + explanation.
  - **Right rail (~40%)**: tinted/contained panel titled **ACTIONS FOR CMOS** — one bold thesis line then 3 icon + action items stacked.
  - Footer page number. The left = diagnosis, right = prescription. Same skeleton every trend → reader learns the template once.
- **CLOSING (p17)** — "Thank you" H1 + contact experts list (name + email), reversed/quiet. Minimal.

### 5. Data-Visual Style

- **No traditional charts** (no bar/line/pie anywhere in the sample). All quantitative content is expressed as **oversized single statistics** ("big number" treatment) rather than plotted data.
- Stats are always: accent-green numeral (largest element) + tiny grey caption + sometimes a line-icon above. Grouped in rows of 4–5 to read as a stat wall.
- Icons are **thin single-weight line icons**, monochrome (ink or accent), one per concept — never filled, never multicolor. They label, not decorate.
- The only "infographic" is the p8 swimlane matrix: flat pill labels in a grid, no color-coding beyond a faint header tint.
- Every data page carries an explicit **`Source:`** line (e.g. "Source: Deloitte CMO Survey 2025") at small size — sourcing is a visible design element, not an afterthought.

### 6. ★ STEAL AS DISCIPLINE (reusable rules for the TickDeck engine)

1. **Count-driven grid.** Let the number of items choose the column count (3 items → 3 cols, 5 → 5). Equal widths, even gutters, icon-on-top cells. Stops the engine from cramming uneven content.
2. **One-accent monochrome system.** Paper + ink + exactly ONE saturated accent. Reserve the accent for headlines and the single most important number per cell. Everything else is ink/grey. (Apply with OUR brand hue, not Deloitte green — `[브랜드전용·복제금지]`.)
3. **Big-number-as-hero for any statistic.** When a slide has a key figure, render it at ~3–5× body size in the accent color, with a 2-line grey explainer beneath. Never bury a stat in a sentence.
4. **Persistent positional rhythm.** H1 always top-left in the same band; footer (page # + source) always on the same baseline; margins identical every page. Flipping the deck should feel like one spine.
5. **Repeatable body template for series content.** For N parallel sections (our "trends/points"), use ONE fixed two-zone skeleton — left = diagnosis (what we see / drivers), right = prescription (actions) — and repeat it verbatim. Consistency > novelty per slide.
6. **Divider pages earn their vividness.** Insert a full-bleed dark "statement" slide with a single large reversed headline before each major section; keep ALL color/vibrancy quarantined to these dividers so work pages stay calm. (Use OUR abstract art, not their swirl renders — `[브랜드전용·복제금지]`.)
7. **Mandatory visible source line.** Any slide with data gets a small `Source:` caption on a fixed baseline. Makes the deck credible and gives the engine a defined slot instead of dropping citations.
8. **Weight-mixing for headline emphasis.** Emphasize within a headline by switching weight (bold key words, light connectives) on a single type size — instead of changing color or size. Cheaper, calmer, on-brand.

---

## PART B — CONTENT FACTS (one claim = one source page)

**Macro / economic context**
- European economies are in a sustained low-growth cycle with uneven demand and fragile confidence; constraints (not innovation) now define the market. (p.3)
- EU inflation remains above pre-pandemic levels, curbing purchasing power and making consumers more selective. (p.3)
- Marketing budgets face stronger CFO oversight and demand finance-grade measurement; efficiency/accountability now outweigh ambition. (p.3)

**Changing consumers**
- Brands that deliver strong end-to-end experiences see improvement on customer satisfaction and conversion metrics. (p.5) — *note: page shows stat band 40% / 43% / 20% associated with these consumer-shift columns; exact metric-to-number mapping not fully legible, cite figures as presented on p.5.*
- Four consumer shifts: more deliberate (not disengaged); value is reinterpreted (will pay more when benefit is clear); experiences set cross-category expectations; discovery shifting to content/recommendations/communities. (p.5)

**AI in marketing — five truths (p.7)**
- AI will decimate production cost: **+200% copy capacity**, **~60% less manual design time**, cost per image **≈ €45 → €4–6**. (p.7)
- Hyper-personalised content outperforms basic: **site conversion 2.9% vs 0.5%**; **email CTR 3.4% vs 1.8%**; personalised video ads **44% VTR**. (p.7)
- Trust caveat: **only 42% of consumers trust businesses to use AI ethically**. (p.7)
- **Only 10% of organisations** are realising significant ROI from agentic AI (Deloitte 2025 survey of **1,854 executives across EMEA**). (p.7)
- **85% of organisations increased AI investment in the past 12 months; 91% plan further increases**; satisfactory ROI often takes **2–4 years**. (p.7)

**AI changing how marketing works — GenAI use-case uplifts (p.8, Source: Deloitte Genie Analysis 2025)**
- **+48%** revenue growth from capturing priority customer segments. (p.8)
- **300X** improvement in article-development velocity with GenAI. (p.8)
- **+50%** increase in CTR through personalised communications. (p.8)
- **+36%** potential time savings from optimising audiences and journey designs. (p.8)
- **100X** increase in production speed for content creation. (p.8)

**CMO realities (p.9, Source: Deloitte CMO Survey 2025)**
- **33%** of CMOs prioritise profitability, vs **67%** of C-suite peers. (p.9)
- **64%** of CMOs say proving marketing's value to the business is their biggest challenge. (p.9)
- **1 in 6** marketing activities use AI today; set to **more than double in the next 3 years**. (p.9)
- **62%** of CMOs say finding the right external people is their biggest talent challenge. (p.9)

**MarTech investment (p.10, Source: Deloitte CMO Survey 2025)**
- Orgs investing more in MarTech than working media see **18% greater sales lift** and **7% greater revenue growth** than those favouring working media. (p.10)
- **At least 61% of marketing budgets** are set off enterprise-level revenue/budgets or prior spend, leaving marketers limited control over inputs. (p.10)

**The five 2026 trends (p.11)**
1. AI becomes the operating system of marketing; 2. Performance, ROI & the end of "blind" marketing spend; 3. Trust, brand & purpose become economic assets; 4. Channel fragmentation & reinvention of brand discovery; 5. The marketing organisation is being rebuilt. (p.11)

**Trend deep-dive figures**
- **Only 33% of enterprises currently have KPI targets for marketing ROI** (expected to rise as boards demand measurable revenue contribution). (p.13)
- Retail media networks: **EU spend nearing €18B in 2025**, redirecting spend from other channels. (p.15)
- **72% increase in influencer marketing spend**, driven by social-first / creator-led discovery. (p.15)
- Org rebuild: **93% surge in content needs** overwhelming team capacity. (p.16)

---

### Notes / limits
- No conventional charts exist in this deck; all "data viz" = oversized single statistics. The engine should treat "big number" as the primary data primitive.
- p5's stat band (40% / 43% / 20%) labels were partly cut in the text layer; figures cited as they appear but exact metric pairing should be re-verified against the source PDF before reuse.
- All hex values are visual approximations from rendered pages, not extracted swatches. Deloitte deep green (~#046A38) is brand-owned — borrow the *one-accent* rule, not the hue.
