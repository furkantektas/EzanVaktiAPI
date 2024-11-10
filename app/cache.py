import redis

from .config import get_settings

cache = redis.StrictRedis.from_url(get_settings().redis_url, decode_responses=False)
