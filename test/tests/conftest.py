import pytest
import telegram
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path
import time
import redis.exceptions
import logging

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import db
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType

def create_indices(redis_client):
    """Explicitly create Redis indices"""
    logger.debug("Creating Redis indices...")
    
    # Create session index
    try:
        sess_index = redis_client.ft('idx:session')
        sess_index.info()
        logger.debug("Session index already exists")
    except:
        logger.debug("Creating session index")
        sess_index = redis_client.ft('idx:session')
        sess_schema = (
            NumericField('usr_id'),
            NumericField('chat_id'),
            NumericField('msg_id'),
            NumericField('ts'),
        )
        sess_index.create_index(
            sess_schema,
            definition=IndexDefinition(prefix=['session:'], index_type=IndexType.HASH)
        )
        logger.debug("Session index created successfully")

    # Create point index
    try:
        point_index = redis_client.ft('idx:point')
        point_index.info()
        logger.debug("Point index already exists")
    except:
        logger.debug("Creating point index")
        point_index = redis_client.ft('idx:point')
        point_schema = (
            TagField('sess_id'),
            NumericField('ts'),
        )
        point_index.create_index(
            point_schema,
            definition=IndexDefinition(prefix=['point:'], index_type=IndexType.HASH)
        )
        logger.debug("Point index created successfully")

def wait_for_redis(max_retries=30, delay=1):
    """Wait for Redis to be ready and create indices"""
    logger.debug("Waiting for Redis to be ready...")
    for i in range(max_retries):
        try:
            redis = db.get_redis()
            redis.ping()
            logger.debug("Redis ping successful")
            create_indices(redis)
            return redis
        except (redis.exceptions.ConnectionError, redis.exceptions.ResponseError) as e:
            logger.debug(f"Attempt {i+1}/{max_retries} failed: {str(e)}")
            if i == max_retries - 1:
                raise
            time.sleep(delay)
    raise Exception("Redis failed to become ready")

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
    create_indices(redis_connection)
    yield redis_connection
    logger.info("CLEANING UP TEST DATABASE")
    redis_connection.flushall()

@pytest.fixture
def mock_update():
    """Create a mock Telegram Update object"""
    update = MagicMock(spec=telegram.Update)
    update.effective_user = MagicMock(spec=telegram.User)
    update.effective_user.id = 12345
    update.effective_user.first_name = "Test User"
    
    update.message = MagicMock(spec=telegram.Message)
    update.message.chat = MagicMock(spec=telegram.Chat)
    update.message.chat.id = 67890
    update.message.chat.type = "private"
    update.message.chat.title = None
    update.message.chat.username = "test_user"
    update.message.message_id = 100
    update.message.from_user = update.effective_user
    update.message.date = MagicMock()
    update.message.date.timestamp.return_value = 1234567890
    
    update.edited_message = None
    update.effective_chat = update.message.chat
    
    return update

@pytest.fixture
def mock_context():
    """Create a mock Telegram Context object"""
    context = MagicMock(spec=telegram.ext.ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock(spec=telegram.Bot)
    return context

@pytest.fixture
def mock_location():
    """Create a mock Location object"""
    location = MagicMock(spec=telegram.Location)
    location.latitude = 55.7558
    location.longitude = 37.6173
    location.live_period = 3600
    return location 