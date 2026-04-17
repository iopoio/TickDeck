import React, { useState } from 'react';

interface HomePageProps {
  onGenerate: (url: string, language: string) => void;
  isLoading: boolean;
  error: string | null;
}

const HomePage: React.FC<HomePageProps> = ({ onGenerate, isLoading, error }) => {
  const [url, setUrl] = useState<string>('');
  const [language, setLanguage] = useState<string>('ko');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (url.trim()) {
      onGenerate(url, language);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-screen w-full bg-white px-4">
      <div className="flex flex-col items-center w-full max-w-xl text-center space-y-10">
        <div className="space-y-3">
          <h1 className="text-3xl font-bold text-brand">TickDeck</h1>
          <p className="text-gray-500 text-lg">URL 하나로 프레젠테이션 완성</p>
        </div>

        <form onSubmit={handleSubmit} className="flex flex-col items-center w-full space-y-8">
          <input
            type="url"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com"
            className="w-full px-6 py-4 text-lg border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-brand focus:border-transparent transition-all shadow-sm"
            required
          />

          <div className="flex items-center space-x-10">
            <label className="flex items-center space-x-3 cursor-pointer group">
              <input
                type="radio"
                name="language"
                value="ko"
                checked={language === 'ko'}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-5 h-5 text-brand border-gray-300 focus:ring-brand cursor-pointer"
              />
              <span className="text-gray-700 font-medium group-hover:text-brand transition-colors">한국어</span>
            </label>
            <label className="flex items-center space-x-3 cursor-pointer group">
              <input
                type="radio"
                name="language"
                value="en"
                checked={language === 'en'}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-5 h-5 text-brand border-gray-300 focus:ring-brand cursor-pointer"
              />
              <span className="text-gray-700 font-medium group-hover:text-brand transition-colors">English</span>
            </label>
          </div>

          {error && <p className="text-red-500 font-medium">{error}</p>}

          <button
            type="submit"
            disabled={isLoading || !url.trim()}
            className="bg-brand text-white text-lg font-bold rounded-xl px-12 py-4 shadow-lg hover:brightness-110 active:scale-95 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all w-full md:w-auto"
          >
            {isLoading ? '생성 중...' : '슬라이드 생성'}
          </button>
        </form>
      </div>
    </div>
  );
};

export default HomePage;
