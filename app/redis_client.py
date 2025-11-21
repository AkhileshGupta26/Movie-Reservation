import redis
from .config import settings
import logging

logger = logging.getLogger(__name__)

try:
    redis_client = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True)
    redis_client.ping()
except Exception as e:
    logger.warning(f"Redis connection failed: {e}. Running without Redis cache.")
    redis_client = None
