import redis

from shared.constants.config import REDIS_URL

redis_client = redis.Redis.from_url(REDIS_URL)
