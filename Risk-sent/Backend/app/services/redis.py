import redis.asyncio as redis
from app.core.config import settings
from app.core.logging import logging

logger = logging.getLogger(__name__)

REDIS_CONNECTION_URL = settings.REDIS_SERVER_URL
try : 
 redis_client = redis.from_url(REDIS_CONNECTION_URL , decode_responses=True)
 logger.info("Connected to redis server")
except Exception as e :
    logger.error("Error connecting to redis server " , str(e)) 

