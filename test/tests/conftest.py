import pytest
import telegram
from unittest.mock import AsyncMock, MagicMock
import datetime
import time
import redis.exceptions
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

import db
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

def wait_for_redis(max_retries=30, delay=1):
    """Wait for Redis to be ready and create indices"""
    logger.debug("Waiting for Redis to be ready...")
    for i in range(max_retries):
        try:
            redis = db.get_redis()
            redis.ping()
            logger.debug("Redis ping successful")
            return redis
        except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError) as e:
            logger.debug(f"Attempt {i+1}/{max_retries} failed: {str(e)}")
            time.sleep(delay)
    raise Exception("Redis failed to become ready")


def create_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


@pytest.fixture(scope="session")
def redis_connection():
    """Create Redis connection"""
    logger.info("SETTING UP REDIS CONNECTION")
    redis = wait_for_redis()
    logger.info("REDIS CONNECTION ESTABLISHED")
    return redis


@pytest.fixture(autouse=True)
def setup_test_db(redis_connection):
    """Setup test database before each test"""
    logger.info("SETTING UP TEST DATABASE")
    redis_connection.flushall()
    db.setup_redis()
    yield redis_connection
    logger.info("CLEANING UP TEST DATABASE")
    redis_connection.flushall()


@pytest.fixture
def mock_update_factory():
    """Create a mock Telegram Update object"""
    def _factory():
        update = MagicMock(spec=telegram.Update)
        
        update.message = MagicMock(spec=telegram.Message)
        update.message.chat = MagicMock(spec=telegram.Chat)
        update.message.chat.id = 67890
        update.message.chat.type = "private"
        update.message.chat.title = None
        update.message.chat.username = "test_user"
        update.message.message_id = 100
        update.message.from_user = MagicMock(spec=telegram.User)
        update.message.from_user.id = 12345
        update.message.from_user.first_name = "Test User"
        update.message.date = create_datetime("2025-05-17 12:20:00")
        
        update.edited_message = None
        update.effective_chat = update.message.chat
        update.effective_user = update.message.from_user
        return update
    return _factory


@pytest.fixture
def mock_context():
    """Create a mock Telegram Context object"""
    context = MagicMock(spec=telegram.ext.ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock(spec=telegram.Bot)
    return context


@pytest.fixture
def mock_location_factory():
    def _factory(latitude=45.2393, longitude=19.8412, live_period=3600):
        location = MagicMock(spec=telegram.Location)
        location.latitude = latitude
        location.longitude = longitude
        location.live_period = live_period
        return location
    return _factory
