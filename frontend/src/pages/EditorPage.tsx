import React, { useState } from 'react';
import type { SlideContent, SlideItem } from '../types';

interface EditorPageProps {
  slideContent: SlideContent;
  onConfirm: (content: SlideContent) => void;
  isConfirming: boolean;
}

const SLIDE_TYPE_LABELS: Record<string, string> = {
  cover: '커버',
  section_intro: '섹션 소개',
  content: '콘텐츠',
  key_metrics: '핵심 지표',
  cta: 'CTA',
};

const EditorPage: React.FC<EditorPageProps> = ({ slideContent, onConfirm, isConfirming }) => {
  const [content, setContent] = useState<SlideContent>(slideContent);
  const [selectedIdx, setSelectedIdx] = useState<number>(0);

  const updateSlide = (idx: number, field: keyof SlideItem, value: string | string[]) => {
    setContent((prev) => {
      const slides = [...prev.slides];
      slides[idx] = { ...slides[idx], [field]: value };
      return { ...prev, slides };
    });
  };

  const updateBody = (idx: number, bodyIdx: number, value: string) => {
    setContent((prev) => {
      const slides = [...prev.slides];
      const body = [...slides[idx].body];
      body[bodyIdx] = value;
      slides[idx] = { ...slides[idx], body };
      return { ...prev, slides };
    });
  };

  const addBodyItem = (idx: number) => {
    setContent((prev) => {
      const slides = [...prev.slides];
      slides[idx] = { ...slides[idx], body: [...slides[idx].body, ''] };
      return { ...prev, slides };
    });
  };

  const removeBodyItem = (idx: number, bodyIdx: number) => {
    setContent((prev) => {
      const slides = [...prev.slides];
      const body = slides[idx].body.filter((_, i) => i !== bodyIdx);
      slides[idx] = { ...slides[idx], body };
      return { ...prev, slides };
    });
  };

  const selected = content.slides[selectedIdx];

  return (
    <div className="flex flex-col min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-100 px-6 py-4 flex items-center justify-between sticky top-0 z-10">
        <span className="text-lg font-bold text-brand">TickDeck</span>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{content.slides.length}개 슬라이드</span>
          <button
            onClick={() => onConfirm(content)}
            disabled={isConfirming}
            className="bg-brand text-white text-sm font-bold rounded-xl px-6 py-2.5 hover:brightness-110 active:scale-95 disabled:bg-gray-300 disabled:cursor-not-allowed transition-all"
          >
            {isConfirming ? 'PPTX 생성 중...' : 'PPTX 다운로드'}
          </button>
        </div>
      </header>

      <div className="flex flex-1 overflow-hidden">
        {/* 슬라이드 목록 */}
        <aside className="w-48 bg-white border-r border-gray-100 overflow-y-auto flex-shrink-0">
          {content.slides.map((slide, idx) => (
            <button
              key={idx}
              onClick={() => setSelectedIdx(idx)}
              className={`w-full text-left px-4 py-3 border-b border-gray-50 transition-colors ${
                selectedIdx === idx ? 'bg-blue-50 border-l-2 border-l-brand' : 'hover:bg-gray-50'
              }`}
            >
              <div className="text-xs text-gray-400 mb-0.5">{idx + 1} / {SLIDE_TYPE_LABELS[slide.type] || slide.type}</div>
              <div className="text-sm font-medium text-gray-800 truncate">{slide.headline || '(제목 없음)'}</div>
            </button>
          ))}
        </aside>

        {/* 편집 패널 */}
        <main className="flex-1 overflow-y-auto p-6">
          <div className="max-w-2xl mx-auto space-y-6">
            <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-4">
              <div className="flex items-center gap-2">
                <span className="text-xs bg-blue-50 text-brand px-2 py-1 rounded-full font-medium">
                  {SLIDE_TYPE_LABELS[selected.type] || selected.type}
                </span>
                <span className="text-sm text-gray-400">슬라이드 {selectedIdx + 1}</span>
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-500 font-medium">Eyebrow</label>
                <input
                  type="text"
                  value={selected.eyebrow}
                  onChange={(e) => updateSlide(selectedIdx, 'eyebrow', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
                  placeholder="상단 작은 텍스트"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-500 font-medium">헤드라인</label>
                <input
                  type="text"
                  value={selected.headline}
                  onChange={(e) => updateSlide(selectedIdx, 'headline', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand font-semibold"
                  placeholder="슬라이드 제목"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs text-gray-500 font-medium">서브헤드라인</label>
                <input
                  type="text"
                  value={selected.subheadline}
                  onChange={(e) => updateSlide(selectedIdx, 'subheadline', e.target.value)}
                  className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
                  placeholder="부제목"
                />
              </div>

              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs text-gray-500 font-medium">본문 항목</label>
                  <button
                    onClick={() => addBodyItem(selectedIdx)}
                    className="text-xs text-brand hover:underline"
                  >
                    + 추가
                  </button>
                </div>
                {selected.body.map((item, bodyIdx) => (
                  <div key={bodyIdx} className="flex gap-2">
                    <input
                      type="text"
                      value={item}
                      onChange={(e) => updateBody(selectedIdx, bodyIdx, e.target.value)}
                      className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
                      placeholder={`항목 ${bodyIdx + 1}`}
                    />
                    <button
                      onClick={() => removeBodyItem(selectedIdx, bodyIdx)}
                      className="text-gray-300 hover:text-red-400 transition-colors px-1"
                    >
                      ×
                    </button>
                  </div>
                ))}
                {selected.body.length === 0 && (
                  <p className="text-xs text-gray-300 text-center py-2">본문 항목 없음</p>
                )}
              </div>
            </div>

            {/* 브랜드 정보 */}
            <div className="bg-white rounded-2xl border border-gray-100 p-6 space-y-4">
              <h3 className="text-sm font-semibold text-gray-700">브랜드 정보</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 font-medium">회사명</label>
                  <input
                    type="text"
                    value={content.brand.companyName}
                    onChange={(e) =>
                      setContent((prev) => ({ ...prev, brand: { ...prev.brand, companyName: e.target.value } }))
                    }
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
                  />
                </div>
                <div className="space-y-1">
                  <label className="text-xs text-gray-500 font-medium">업종</label>
                  <input
                    type="text"
                    value={content.brand.industry}
                    onChange={(e) =>
                      setContent((prev) => ({ ...prev, brand: { ...prev.brand, industry: e.target.value } }))
                    }
                    className="w-full px-3 py-2 text-sm border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-brand"
                  />
                </div>
              </div>
              <div className="space-y-1">
                <label className="text-xs text-gray-500 font-medium">메인 컬러</label>
                <div className="flex items-center gap-3">
                  <input
                    type="color"
                    value={content.brand.primaryColor}
                    onChange={(e) =>
                      setContent((prev) => ({ ...prev, brand: { ...prev.brand, primaryColor: e.target.value } }))
                    }
                    className="w-10 h-10 rounded-lg border border-gray-200 cursor-pointer"
                  />
                  <span className="text-sm text-gray-500 font-mono">{content.brand.primaryColor}</span>
                </div>
              </div>
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default EditorPage;
