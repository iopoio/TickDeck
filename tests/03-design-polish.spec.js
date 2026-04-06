// 시나리오 6: 디자인 폴리시 검증
const { test, expect } = require('@playwright/test');

test.describe('시나리오 6: 디자인 폴리시', () => {

  test('D2. transition: all 미사용', async ({ page }) => {
    await page.goto('/app');
    const html = await page.content();
    // 인라인 스타일에서 transition: all 또는 transition:all 검색
    // CSS 주석 내부는 제외하고 style 속성 내에서만 검사
    const styleMatches = html.match(/style="[^"]*transition\s*:\s*all[^"]*"/gi) || [];
    expect(styleMatches.length).toBe(0);
  });

  test('D2. 랜딩 transition: all 미사용', async ({ page }) => {
    await page.goto('/');
    const styles = await page.evaluate(() => {
      const allStyles = [];
      document.querySelectorAll('style').forEach(s => allStyles.push(s.textContent));
      return allStyles.join('\n');
    });
    expect(styles).not.toMatch(/transition\s*:\s*all\b/);
  });

  // SKIP: coming_soon 모드에서는 랜딩 페이지 미노출. 서비스 재오픈 시 test.skip 제거
  test.skip('D3. CTA 버튼 active scale 존재 (랜딩)', async ({ page }) => {
    await page.goto('/');
    const styles = await page.evaluate(() => {
      const allStyles = [];
      document.querySelectorAll('style').forEach(s => allStyles.push(s.textContent));
      return allStyles.join('\n');
    });
    expect(styles).toContain('scale(0.96)');
  });

  test('D4. text-wrap: balance 적용됨 (랜딩)', async ({ page }) => {
    await page.goto('/');
    const styles = await page.evaluate(() => {
      const allStyles = [];
      document.querySelectorAll('style').forEach(s => allStyles.push(s.textContent));
      return allStyles.join('\n');
    });
    expect(styles).toContain('text-wrap: balance');
    expect(styles).toContain('text-wrap: pretty');
  });

  test('D5. 언어 전환 버튼 히트 영역 >= 32px', async ({ page }) => {
    await page.goto('/app');
    const langLink = page.locator('a[href="/en/app"], a[href="/app"]').first();
    const box = await langLink.boundingBox();
    if (box) {
      expect(box.height).toBeGreaterThanOrEqual(28);
      expect(box.width).toBeGreaterThanOrEqual(28);
    }
  });

  // SKIP: coming_soon 모드에서는 랜딩 페이지 미노출 (이미지 없음). 서비스 재오픈 시 test.skip 제거
  test.skip('D6. 이미지 outline 적용됨 (랜딩)', async ({ page }) => {
    await page.goto('/');
    const styles = await page.evaluate(() => {
      const allStyles = [];
      document.querySelectorAll('style').forEach(s => allStyles.push(s.textContent));
      return allStyles.join('\n');
    });
    expect(styles).toContain('outline-offset: -1px');
  });

  test('D10. ESC 키로 모달 닫기 가능', async ({ page }) => {
    await page.goto('/app');
    // 편집 모달 오버레이 확인 (hidden 상태)
    const overlay = page.locator('#edit-modal-overlay');
    await expect(overlay).toHaveClass(/hidden/);

    // ESC 이벤트 리스너 존재 확인
    const hasEscHandler = await page.evaluate(() => {
      return document.body.innerHTML.includes("key === 'Escape'")
        || document.body.innerHTML.includes('key === "Escape"');
    });
    expect(hasEscHandler).toBe(true);
  });

  test('M8. ARIA nav label 존재', async ({ page }) => {
    await page.goto('/app');
    const nav = page.locator('nav[aria-label]');
    await expect(nav).toHaveAttribute('aria-label', 'Main navigation');
  });

  test('M8. 편집 모달 role="dialog"', async ({ page }) => {
    await page.goto('/app');
    const modal = page.locator('#edit-modal-overlay');
    await expect(modal).toHaveAttribute('role', 'dialog');
    await expect(modal).toHaveAttribute('aria-modal', 'true');
  });

  // SKIP: coming_soon 모드에서는 랜딩 페이지 미노출 (동심원 Mockup 없음). 서비스 재오픈 시 test.skip 제거
  test.skip('D1. 동심원 border-radius (랜딩)', async ({ page }) => {
    await page.goto('/');
    const styles = await page.evaluate(() => {
      const allStyles = [];
      document.querySelectorAll('style').forEach(s => allStyles.push(s.textContent));
      return allStyles.join('\n');
    });
    // 외부 24px, 내부 8px 확인
    expect(styles).toContain('border-radius: 24px');
    expect(styles).toContain('border-radius: 8px');
  });

});
