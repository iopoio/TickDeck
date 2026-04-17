import type { GenerationStatus, SlideContent } from '../types'

const getHeaders = (token: string) => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${token}`,
})

export async function generateSlide(url: string, language: string, token: string) {
  const res = await fetch('/api/slides/generate', {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify({ url, language }),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '요청 실패' }))
    throw new Error(err.detail || '요청 실패')
  }
  return res.json() as Promise<{ generation_id: string; status: string }>
}

export async function getStatus(generationId: string, token: string): Promise<GenerationStatus> {
  const res = await fetch(`/api/slides/${generationId}/status`, {
    headers: getHeaders(token),
  })
  if (!res.ok) throw new Error('상태 조회 실패')
  return res.json()
}

export async function confirmGeneration(
  generationId: string,
  slideContent: SlideContent,
  token: string
) {
  const res = await fetch(`/api/slides/${generationId}/confirm`, {
    method: 'POST',
    headers: getHeaders(token),
    body: JSON.stringify(slideContent),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: 'PPTX 생성 실패' }))
    throw new Error(err.detail || 'PPTX 생성 실패')
  }
  return res.json()
}

export async function getBalance(token: string) {
  const res = await fetch('/api/tokens/balance', {
    headers: getHeaders(token),
  })
  if (!res.ok) throw new Error('잔액 조회 실패')
  return res.json() as Promise<{ balance: number }>
}

export async function googleLogin() {
  window.location.href = '/api/auth/google'
}
