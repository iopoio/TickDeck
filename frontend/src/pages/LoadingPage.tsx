import React from 'react';

interface LoadingPageProps {
  status: string;
  error: string | null;
  onRetry: () => void;
}

const LoadingPage: React.FC<LoadingPageProps> = ({ status, error, onRetry }) => {
  const getStatusMessage = () => {
    switch (status) {
      case 'pending': return '요청 접수 중...';
      case 'crawling': return '웹페이지 분석 중...';
      case 'structuring': return '슬라이드 구조화 중...';
      default: return '처리 중...';
    }
  };

  const steps = [
    { id: 'crawling', label: '크롤링' },
    { id: 'structuring', label: '구조화' },
    { id: 'ready', label: '편집 준비' },
  ];

  const statusOrder: Record<string, number> = { pending: -1, crawling: 0, structuring: 1, ready: 2 };

  const getStepStyles = (index: number) => {
    const current = statusOrder[status] ?? 0;
    if (status === 'failed') return 'text-gray-300';
    if (current > index) return 'text-brand font-semibold';
    if (current === index) return 'text-brand animate-pulse font-semibold';
    return 'text-gray-300';
  };

  if (status === 'failed') {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen bg-white p-6">
        <div className="text-xl font-bold text-brand mb-12">TickDeck</div>
        <div className="max-w-md w-full text-center space-y-6 bg-red-50 p-8 rounded-2xl border border-red-100">
          <h2 className="text-lg font-bold text-red-700">오류가 발생했습니다</h2>
          <p className="text-sm text-red-600">{error || '알 수 없는 오류'}</p>
          <button
            onClick={onRetry}
            className="w-full py-3 px-4 bg-brand text-white rounded-xl font-bold hover:opacity-90 transition-all active:scale-95"
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white p-6">
      <div className="absolute top-12 text-xl font-bold text-brand">TickDeck</div>
      <div className="flex flex-col items-center space-y-10 max-w-sm w-full">
        <div className="w-20 h-20 border-4 border-gray-100 border-t-brand rounded-full animate-spin" />
        <div className="text-center space-y-2">
          <h2 className="text-2xl font-bold text-gray-900">{getStatusMessage()}</h2>
          <p className="text-gray-500 text-sm">AI가 슬라이드 구조를 생성하고 있습니다.</p>
        </div>
        <div className="flex items-center justify-between w-full px-4 pt-6 border-t border-gray-100">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <span className={`text-sm transition-colors ${getStepStyles(idx)}`}>{step.label}</span>
              {idx < steps.length - 1 && <div className="h-px w-8 bg-gray-100" />}
            </React.Fragment>
          ))}
        </div>
        <p className="text-xs text-gray-400">보통 30초~1분 소요됩니다.</p>
      </div>
    </div>
  );
};

export default LoadingPage;
