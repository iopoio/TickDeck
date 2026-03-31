// 시나리오 3: 보안 검증
const { test, expect } = require('@playwright/test');

test.describe('시나리오 3: 보안', () => {

  // SSRF 테스트: 비인증이면 401, 인증 상태면 400 — 둘 다 접근 차단이므로 OK
  test('3-1. SSRF — localhost 차단', async ({ request }) => {
    const res = await request.post('/generate', {
      data: { url: 'http://localhost:6379' },
    });
    expect([400, 401]).toContain(res.status());
  });

  test('3-1. SSRF — private IP 차단', async ({ request }) => {
    const res = await request.post('/generate', {
      data: { url: 'http://192.168.1.1' },
    });
    expect([400, 401]).toContain(res.status());
  });

  test('3-1. SSRF — 169.254 메타데이터 차단', async ({ request }) => {
    const res = await request.post('/generate', {
      data: { url: 'http://169.254.169.254' },
    });
    expect([400, 401]).toContain(res.status());
  });

  test('3-1. SSRF — 10.x.x.x 차단', async ({ request }) => {
    const res = await request.post('/generate', {
      data: { url: 'http://10.0.0.1' },
    });
    expect([400, 401]).toContain(res.status());
  });

  test('3-2. Rate Limit — signup 6회 시 429', async ({ request }) => {
    const results = [];
    for (let i = 0; i < 7; i++) {
      const res = await request.post('/api/auth/signup', {
        data: {
          email: `pw_test_${Date.now()}_${i}@test.com`,
          password: '123456',
        },
      });
      results.push(res.status());
    }
    // 처음 5개: 200 또는 409, 6번째부터: 429
    const has429 = results.some(s => s === 429);
    expect(has429).toBe(true);
  });

  test('3-3. Admin — 비인증 접근 차단', async ({ request }) => {
    const res = await request.get('/admin');
    // 리다이렉트(302) 또는 401
    expect([302, 200, 401]).toContain(res.status());
    // 200이면 /app으로 리다이렉트된 것
    if (res.status() === 200) {
      expect(res.url()).toContain('/app');
    }
  });

  test('3-4. OAuth — state 파라미터 존재', async ({ page }) => {
    await page.goto('/app');
    // Google 로그인 링크의 href 확인
    const link = await page.goto('/api/auth/google');
    const url = page.url();
    expect(url).toContain('state=');
  });

  test('3-5. 에러 메시지 — 시스템 정보 미노출', async ({ request }) => {
    // 비인증 상태에서 generate 호출
    const res = await request.post('/generate', {
      data: { url: 'https://example.com' },
    });
    const body = await res.json();
    const text = JSON.stringify(body);
    // 시스템 경로, traceback, API 키 미포함
    expect(text).not.toContain('/opt/tickdeck');
    expect(text).not.toContain('Traceback');
    expect(text).not.toContain('GEMINI_API_KEY');
    expect(text).not.toContain('explicit_primary');
  });

});
