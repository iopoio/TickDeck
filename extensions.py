# extensions.py
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

redis_client = None
JOBS = {}
USE_CELERY = False
_log = None
limiter = Limiter(key_func=get_remote_address)
ADMIN_EMAILS = set()
