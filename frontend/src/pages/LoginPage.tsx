import React from 'react';
import { googleLogin } from '../services/api';

const LoginPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-[#F9FAFB] flex flex-col items-center justify-center p-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-xl p-8 border border-gray-100 flex flex-col items-center">
        {/* Logo */}
        <div className="w-16 h-16 bg-indigo-600 rounded-2xl flex items-center justify-center mb-6 shadow-lg shadow-indigo-100">
          <svg className="w-10 h-10 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
          </svg>
        </div>

        <h1 className="text-3xl font-bold text-gray-900 mb-2">TickDeck</h1>
        <p className="text-gray-500 text-center mb-10">
          복잡한 웹사이트를 단 몇 초 만에<br />
          아름다운 슬라이드로 변환하세요.
        </p>

        <button
          onClick={googleLogin}
          className="w-full flex items-center justify-center gap-3 bg-white border border-gray-300 py-3.5 px-4 rounded-xl font-semibold text-gray-700 hover:bg-gray-50 transition-all active:scale-[0.98] shadow-sm"
        >
          <img src="https://www.gstatic.com/firebasejs/ui/2.0.0/images/auth/google.svg" alt="Google" className="w-5 h-5" />
          Google로 시작하기
        </button>

        <p className="mt-8 text-xs text-gray-400 text-center leading-relaxed">
          로그인 시 TickDeck의 이용약관 및 개인정보 처리방침에<br />
          동의하게 됩니다.
        </p>
      </div>
      
      <div className="mt-8 flex gap-6 text-sm text-gray-400">
        <span>서비스 소개</span>
        <span>커뮤니티</span>
        <span>문의하기</span>
      </div>
    </div>
  );
};

export default LoginPage;
