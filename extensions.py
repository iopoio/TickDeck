# extensions.py
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    limiter = Limiter(key_func=get_remote_address)
except ImportError:
    # flask_limiter 미설치 환경 fallback (개발용 NoopLimiter)
    class _NoopLimiter:
        def limit(self, *a, **kw):
            def decorator(f): return f
            return decorator
        def init_app(self, app): pass
    limiter = _NoopLimiter()

redis_client = None
JOBS = {}
USE_CELERY = False
_log = None
ADMIN_EMAILS = set()
