import React from 'react';

interface DonePageProps {
  pptxUrl: string;
  onReset: () => void;
}

const DonePage: React.FC<DonePageProps> = ({ pptxUrl, onReset }) => {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen bg-white p-6">
      <div className="absolute top-12 text-xl font-bold text-brand">TickDeck</div>
      <div className="flex flex-col items-center space-y-8 max-w-sm w-full text-center">
        <div className="w-20 h-20 bg-green-50 rounded-full flex items-center justify-center">
          <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>

        <div className="space-y-2">
          <h2 className="text-2xl font-bold text-gray-900">PPTX 생성 완료!</h2>
          <p className="text-gray-500 text-sm">슬라이드가 성공적으로 만들어졌습니다.</p>
        </div>

        <div className="flex flex-col gap-3 w-full">
          <a
            href={pptxUrl}
            download
            className="w-full py-3 px-4 bg-brand text-white rounded-xl font-bold hover:brightness-110 transition-all active:scale-95 text-center"
          >
            PPTX 다운로드
          </a>
          <button
            onClick={onReset}
            className="w-full py-3 px-4 border border-gray-200 text-gray-600 rounded-xl font-medium hover:bg-gray-50 transition-all"
          >
            새 슬라이드 만들기
          </button>
        </div>
      </div>
    </div>
  );
};

export default DonePage;
