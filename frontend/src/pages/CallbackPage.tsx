import React, { useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { setToken } from '../lib/auth';

const CallbackPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const params = new URLSearchParams(location.search);
    const accessToken = params.get('access_token');
    // refresh_token도 받을 수 있으나 현재는 access_token만 사용
    
    if (accessToken) {
      setToken(accessToken);
      // 로그인 성공 시 홈으로
      navigate('/', { replace: true });
    } else {
      console.error('OAuth callback failed: No access token found');
      navigate('/login', { replace: true });
    }
  }, [location, navigate]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="flex flex-col items-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mb-4"></div>
        <p className="text-gray-600 font-medium">로그인 처리 중...</p>
      </div>
    </div>
  );
};

export default CallbackPage;
