/**
 * stitch_generate.js
 * Google Stitch API로 슬라이드 레이아웃 HTML 템플릿 생성 (개발 시 1회 실행)
 *
 * 사전 준비:
 *   npm install @google/stitch-sdk node-fetch
 *   export STITCH_API_KEY=your_api_key
 *   export STITCH_PROJECT_ID=your_project_id  (Stitch 웹에서 프로젝트 생성 후 확인)
 *
 * 실행:
 *   node stitch_generate.js
 *
 * 결과:
 *   ./static/stitch_templates.json  ← index.html에서 fetch로 로드
 */

import { StitchToolClient } from '@google/stitch-sdk';
import { writeFileSync, mkdirSync } from 'fs';

// ── 레이아웃별 Stitch 프롬프트 ──────────────────────────────────────
const LAYOUTS = {
  cover: `
    A professional 16:9 presentation cover slide with dark navy background.
    Full-width design. Left side: thin vertical purple accent bar (full height, 4px wide).
    Center-left content area: company name in small light grey text at top,
    large bold white headline (2 lines max) in the middle,
    lighter grey subtitle below the headline.
    Bottom: thin horizontal accent line in purple.
    Page number "1" in small grey text at bottom right.
    Clean, minimal, corporate style. No extra decorations.
    Use CSS class names: .slide-company, .slide-headline, .slide-sub, .slide-accent-bar, .slide-page-num
  `,

  split: `
    A professional 16:9 presentation slide split into two vertical panels.
    Left panel (62% width): dark grey image placeholder area, full height.
    Right panel (38% width): white/very light grey background with left padding.
      - Small uppercase purple eyebrow text at top (letter-spacing: 2px)
      - Bold dark headline below (2 lines)
      - 3 bullet point items with dash prefix below the headline
      - Thin left border in purple on the panel edge
    Minimal, clean corporate design.
    CSS classes: .slide-eyebrow, .slide-headline, .slide-body, .slide-img-side, .slide-text-panel
  `,

  cards: `
    A professional 16:9 presentation slide with white/light grey background.
    Top section: small uppercase purple eyebrow label, bold dark headline below.
    Main area: 3 equal-width cards side by side with subtle border and rounded corners.
      Each card: numbered badge (01/02/03) in purple rounded rectangle at top,
      bold card title, 2 lines of description text in grey.
    Clean flat design, no shadows, minimal.
    CSS classes: .slide-eyebrow, .slide-headline, .card-grid, .card-item, .card-num, .card-title, .card-body
  `,

  portfolio: `
    A professional 16:9 presentation slide for portfolio/showcase.
    Full-slide dark background with subtle overlay (represents a background image).
    Bottom-left area (65% width, 40% height): semi-transparent dark glass box
      with 3px left border in purple, white bold headline, 3 white bullet items below.
    Top right: small page number.
    Elegant, dark, high-contrast design.
    CSS classes: .slide-glass-box, .slide-headline, .slide-body, .slide-accent-border, .slide-page-num
  `,

  cta: `
    A professional 16:9 presentation CTA (call-to-action) closing slide.
    Dark navy background. Centered content layout.
    Small decorative circle element (very large, transparent) at top-right as background decoration.
    Left vertical purple accent bar (full height, 4px).
    Content centered: small uppercase purple eyebrow text, large bold white headline (2 lines),
    grey subtitle below, then a small purple horizontal accent line.
    Minimal, impactful design.
    CSS classes: .slide-eyebrow, .slide-headline, .slide-sub, .slide-deco-circle, .slide-accent-bar
  `,
};

// ── placeholder 주입 ─────────────────────────────────────────────────
function injectPlaceholders(html) {
  // Stitch가 생성한 더미 텍스트를 placeholder로 교체
  // 첫 번째 큰 텍스트 요소 → {{HEADLINE}}
  // 첫 번째 작은 텍스트 → {{EYEBROW}} 등
  // 실제 치환은 간단한 규칙 기반으로:
  return html
    // 헤드라인: 가장 큰 폰트 요소로 추정되는 텍스트
    .replace(/(<[^>]*class="[^"]*slide-headline[^"]*"[^>]*>)[^<]*/gi, '$1{{HEADLINE}}')
    .replace(/(<[^>]*class="[^"]*slide-eyebrow[^"]*"[^>]*>)[^<]*/gi, '$1{{EYEBROW}}')
    .replace(/(<[^>]*class="[^"]*slide-sub[^"]*"[^>]*>)[^<]*/gi, '$1{{SUBHEADLINE}}')
    .replace(/(<[^>]*class="[^"]*slide-company[^"]*"[^>]*>)[^<]*/gi, '$1{{COMPANY}}')
    .replace(/(<[^>]*class="[^"]*slide-page-num[^"]*"[^>]*>)[^<]*/gi, '$1{{PAGE_NUM}}');
}

function processTemplate(html) {
  // <style> + <body> 내용 추출 (full HTML page → embeddable snippet)
  const styleMatch = html.match(/<style[^>]*>([\s\S]*?)<\/style>/gi) || [];
  const bodyMatch  = html.match(/<body[^>]*>([\s\S]*?)<\/body>/i);
  const styles     = styleMatch.join('\n');
  const body       = bodyMatch ? bodyMatch[1] : html;

  // purple 계열 색상을 CSS 변수로 교체
  const processed  = (styles + '\n' + body)
    .replace(/#[6-9a-f][0-9a-f][0-9a-f0-9a-f]{3,5}/gi, (m) => {
      // purple/violet 계열만 --accent으로 교체
      const r = parseInt(m.slice(1,3), 16);
      const b = parseInt(m.slice(5,7), 16);
      if (b > r * 1.2 && b > 100) return 'var(--accent, #7c5cf6)';
      return m;
    });

  return `<style>
  :root { --accent: {{ACCENT_COLOR}}; }
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 960px; height: 540px; overflow: hidden;
    font-family: 'Pretendard', -apple-system, 'Malgun Gothic', sans-serif; }
</style>
${injectPlaceholders(processed)}`;
}

// ── 메인 ─────────────────────────────────────────────────────────────
async function main() {
  const projectId = process.env.STITCH_PROJECT_ID;
  if (!process.env.STITCH_API_KEY) {
    console.error('STITCH_API_KEY 환경변수를 설정해주세요.');
    process.exit(1);
  }
  if (!projectId) {
    console.error('STITCH_PROJECT_ID 환경변수를 설정해주세요.');
    console.error('  Stitch 웹(stitch.withgoogle.com)에서 프로젝트 생성 후 URL에서 ID 확인');
    process.exit(1);
  }

  const templates = {};

  for (const [layout, prompt] of Object.entries(LAYOUTS)) {
    console.log(`\n[${layout}] 생성 중...`);
    // 매 호출마다 새 클라이언트 — transport 오염 방지
    const client = new StitchToolClient({ apiKey: process.env.STITCH_API_KEY });
    try {
      const raw = await client.callTool('generate_screen_from_text', {
        projectId,
        prompt: prompt.trim(),
      });

      // outputComponents 중 design.screens 가 있는 것을 찾음
      const comp       = (raw.outputComponents || []).find(c => c.design?.screens?.length);
      const screenData = comp?.design?.screens?.[0];
      if (!screenData) throw new Error('응답에 screen 데이터 없음');

      const htmlUrl = screenData.htmlCode?.downloadUrl;
      if (!htmlUrl) throw new Error('HTML download URL 없음');

      // HTML 다운로드 (Node 24 내장 fetch 사용)
      const res  = await fetch(htmlUrl);
      const html = await res.text();

      templates[layout] = processTemplate(html);
      console.log(`[${layout}] 완료 ✓`);
    } catch (err) {
      console.error(`[${layout}] 실패:`, err.message);
      // 실패 시 텍스트만 있는 fallback 템플릿
      templates[layout] = '<div style="width:960px;height:540px;background:#07071e;display:flex;align-items:center;justify-content:center;color:#fff;font-size:32px;font-weight:700;padding:40px">{{HEADLINE}}</div>';
    } finally {
      await client.close();
    }
  }

  mkdirSync('./static', { recursive: true });
  writeFileSync('./static/stitch_templates.json', JSON.stringify(templates, null, 2), 'utf-8');
  console.log('\n완료! ./static/stitch_templates.json 저장됨');
  console.log('Flask 서버 재시작 후 슬라이드 미리보기 확인하세요.');
}

main().catch(console.error);
