import { useState, useEffect, useCallback } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import HomePage from './pages/HomePage';
import LoadingPage from './pages/LoadingPage';
import EditorPage from './pages/EditorPage';
import DonePage from './pages/DonePage';
import LoginPage from './pages/LoginPage';
import CallbackPage from './pages/CallbackPage';
import { generateSlide, getStatus, confirmGeneration, getBalance } from './services/api';
import { getToken, isLoggedIn, clearToken } from './lib/auth';
import type { SlideContent, GenerationStatus } from './types';

type AppState = 'home' | 'loading' | 'editor' | 'confirming' | 'done';

const POLL_INTERVAL_MS = 3000;

export default function App() {
  const [appState, setAppState] = useState<AppState>('home');
  const [generationId, setGenerationId] = useState<string | null>(null);
  const [genStatus, setGenStatus] = useState<GenerationStatus | null>(null);
  const [slideContent, setSlideContent] = useState<SlideContent | null>(null);
  const [pptxUrl, setPptxUrl] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [balance, setBalance] = useState<number | null>(null);

  const fetchBalance = useCallback(async () => {
    const token = getToken();
    if (!token) return;
    try {
      const data = await getBalance(token);
      setBalance(data.balance);
    } catch {
      // 잔액 조회 실패시 무시
    }
  }, []);

  useEffect(() => {
    if (isLoggedIn()) {
      fetchBalance();
    }
  }, [fetchBalance]);

  const handleGenerate = async (url: string, language: string) => {
    setError(null);
    setIsLoading(true);
    try {
      const token = getToken();
      if (!token) throw new Error('로그인이 필요합니다');
      const result = await generateSlide(url, language, token);
      setGenerationId(result.generation_id);
      setAppState('loading');
      fetchBalance(); // 차감 반영
    } catch (e) {
      setError(e instanceof Error ? e.message : '요청 실패');
    } finally {
      setIsLoading(false);
    }
  };

  const pollStatus = useCallback(async () => {
    if (!generationId) return;
    try {
      const token = getToken();
      if (!token) return;
      const status = await getStatus(generationId, token);
      setGenStatus(status);

      if (status.status === 'ready_to_edit' && status.slide_content) {
        setSlideContent(status.slide_content);
        setAppState('editor');
      } else if (status.status === 'done' && status.pptx_url) {
        setPptxUrl(status.pptx_url);
        setAppState('done');
      } else if (status.status === 'failed') {
        setError(status.error_message || '처리 중 오류가 발생했습니다');
      }
    } catch {
      // 폴링 실패는 조용히 무시 (다음 interval에서 재시도)
    }
  }, [generationId]);

  useEffect(() => {
    if (appState !== 'loading' || !generationId) return;
    pollStatus();
    const interval = setInterval(pollStatus, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
  }, [appState, generationId, pollStatus]);

  const handleConfirm = async (content: SlideContent) => {
    if (!generationId) return;
    setAppState('confirming');
    try {
      const token = getToken();
      if (!token) throw new Error('로그인이 필요합니다');
      const result = await confirmGeneration(generationId, content, token);
      if (result.pptx_url) {
        setPptxUrl(result.pptx_url);
        setAppState('done');
      } else {
        // PPTX 빌드 중 → 폴링 재시작
        setAppState('loading');
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : 'PPTX 생성 실패');
      setAppState('editor');
    }
  };

  const handleReset = () => {
    setAppState('home');
    setGenerationId(null);
    setGenStatus(null);
    setSlideContent(null);
    setPptxUrl(null);
    setError(null);
  };

  const handleRetry = () => {
    handleReset();
  };

  const handleLogout = () => {
    clearToken();
    window.location.href = '/';
  };

  const MainApp = () => {
    if (appState === 'home') {
      return (
        <>
          <div className="absolute top-4 right-4 z-10 flex items-center gap-4">
            {balance !== null && (
              <span className="text-sm font-medium text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full">
                토큰: {balance}개
              </span>
            )}
            <button 
              onClick={handleLogout}
              className="text-xs text-gray-400 hover:text-gray-600 underline"
            >
              로그아웃
            </button>
          </div>
          <HomePage onGenerate={handleGenerate} isLoading={isLoading} error={error} />
        </>
      );
    }

    if (appState === 'loading' || appState === 'confirming') {
      const status = appState === 'confirming' ? 'building_pptx' : (genStatus?.status ?? 'pending');
      const isFailed = genStatus?.status === 'failed';
      return (
        <LoadingPage
          status={isFailed ? 'failed' : status}
          error={error}
          onRetry={handleRetry}
        />
      );
    }

    if (appState === 'editor' && slideContent) {
      return (
        <EditorPage
          slideContent={slideContent}
          onConfirm={handleConfirm}
          isConfirming={false}
        />
      );
    }

    if (appState === 'done' && pptxUrl) {
      return <DonePage pptxUrl={pptxUrl} onReset={handleReset} />;
    }

    return <HomePage onGenerate={handleGenerate} isLoading={isLoading} error={error} />;
  };

  return (
    <Routes>
      <Route path="/login" element={isLoggedIn() ? <Navigate to="/" /> : <LoginPage />} />
      <Route path="/auth/callback" element={<CallbackPage />} />
      <Route 
        path="/" 
        element={isLoggedIn() ? <MainApp /> : <Navigate to="/login" />} 
      />
      <Route path="*" element={<Navigate to="/" />} />
    </Routes>
  );
}
