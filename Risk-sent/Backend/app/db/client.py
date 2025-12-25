from app.core.config import settings
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.logging import logger


class MongoClient:
    def __init__(self):
        self.client = None
        self.db = None

    async def connect(self):
        """
        Called on FastAPI startup
        """
        self.client = AsyncIOMotorClient(
            settings.MONGO_DB_CONNECTION_STRING,
            maxPoolSize=10,
            minPoolSize=1,
            serverSelectionTimeoutMS=5000
        )
        logger.info("Database connected")
        self.db = self.client[settings.MONGO_DB_NAME]


    async def close(self):
        """
        Called on FastAPI shutdown
        """
        if self.client:
            self.client.close()

    def get_db(self):
        """
        Used by repositories/services
        """
        if self.db is None:
            logger.error("Database not connected")
            raise RuntimeError("Database not connected")
        return self.db



mongo_client = MongoClient()


