// 시나리오 1: 기본 접근 + i18n 검증
const { test, expect } = require('@playwright/test');

test.describe('시나리오 1: 기본 접근 + i18n', () => {

  test('1-1. KO 랜딩 페이지 접근', async ({ page }) => {
    const res = await page.goto('/');
    expect(res.status()).toBe(200);
    await expect(page).toHaveTitle(/TickDeck/);
  });

  test('1-1. KO 앱 페이지 접근', async ({ page }) => {
    const res = await page.goto('/app');
    expect(res.status()).toBe(200);
    await expect(page).toHaveTitle(/당신의 웹사이트를 PPT로/);
  });

  test('1-1. KO 텍스트 검증', async ({ page }) => {
    await page.goto('/app');

    // 히어로
    await expect(page.locator('h1')).toContainText('당신의 웹사이트를 PPT로');

    // 로그인 섹션
    await expect(page.locator('text=시작하기')).toBeVisible();
    await expect(page.locator('text=Google로 계속하기')).toBeVisible();

    // 하단 가이드
    await expect(page.locator('text=웹사이트 분석')).toBeVisible();
    await expect(page.locator('text=AI 슬라이드 제작')).toBeVisible();
    await expect(page.locator('text=PPT 다운로드')).toBeVisible();

    // 푸터 (정확한 선택자 — 모달 내부 텍스트와 중복 방지)
    await expect(page.locator('button:has-text("💬 피드백")')).toBeVisible();
    await expect(page.locator('button:has-text("☕ 후원")')).toBeVisible();
  });

  test('1-1. KO Jinja2 변수 미노출', async ({ page }) => {
    await page.goto('/app');
    const html = await page.content();
    expect(html).not.toContain('{{ t.');
    expect(html).not.toContain('{{t.');
  });

  test('1-2. EN 랜딩 페이지 접근', async ({ page }) => {
    const res = await page.goto('/en');
    expect(res.status()).toBe(200);
  });

  test('1-2. EN 앱 페이지 접근', async ({ page }) => {
    const res = await page.goto('/en/app');
    expect(res.status()).toBe(200);
    await expect(page).toHaveTitle(/Turn Your Website into a PPT/);
  });

  test('1-2. EN 텍스트 검증', async ({ page }) => {
    await page.goto('/en/app');

    await expect(page.locator('h1')).toContainText('Turn Your Website into a PPT');
    await expect(page.locator('text=Get Started')).toBeVisible();
    await expect(page.locator('text=Continue with Google')).toBeVisible();
    // Generate Slides는 로그인 후에만 보이므로 HTML에 존재하는지만 확인
    const html = await page.content();
    expect(html).toContain('Generate Slides');
    await expect(page.locator('button:has-text("Feedback")')).toBeVisible();
    await expect(page.locator('button:has-text("Support")')).toBeVisible();
  });

  test('1-2. EN 한글 미혼입 (편집 모달 라벨)', async ({ page }) => {
    await page.goto('/en/app');
    const html = await page.content();

    // 편집 모달 내 한글 금지 항목
    expect(html).not.toMatch(/label[^>]*>헤드라인</);
    expect(html).not.toMatch(/label[^>]*>서브헤드라인</);
    expect(html).not.toContain('>취소<');
    expect(html).not.toContain('>저장<');
    expect(html).not.toContain('AI 재생성');

    // 에러 모달
    expect(html).not.toContain('아래 오류 내용을 확인해주세요');

    // 올바른 영문 확인
    expect(html).toContain('Headline');
    expect(html).toContain('Cancel');
    expect(html).toContain('Save');
    expect(html).toContain('AI Regenerate');
  });

  test('1-2. EN Jinja2 변수 미노출', async ({ page }) => {
    await page.goto('/en/app');
    const html = await page.content();
    expect(html).not.toContain('{{ t.');
  });

});
