import pytest
import telegram
from unittest.mock import AsyncMock, MagicMock
import test_utils
import time
import datetime
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


@pytest.fixture(scope="session")
def redis_connection():
    logger.info("SETTING UP REDIS CONNECTION")
    redis = wait_for_redis()
    logger.info("REDIS CONNECTION ESTABLISHED")
    return redis


@pytest.fixture(autouse=True)
def setup_test_db(redis_connection):
    logger.info("SETTING UP TEST DATABASE")
    redis_connection.flushall()
    db.setup_redis()
    yield redis_connection
    logger.info("CLEANING UP TEST DATABASE")
    redis_connection.flushall()


def create_tg_update():
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
        update.message.date = test_utils.create_datetime("2025-05-17 12:20:00")
        update.message.edit_date = None
        
        update.edited_message = None
        update.effective_chat = update.message.chat
        update.effective_user = update.message.from_user
        return update


def create_tg_location(latitude=45.2393, longitude=19.8412, live_period=3600):
        location = MagicMock(spec=telegram.Location)
        location.latitude = latitude
        location.longitude = longitude
        location.live_period = live_period
        return location


def create_tg_start_update(point: db.TrackPoint):
    result = create_tg_update()
    result.message.location = create_tg_location(point.lat, point.lon, live_period=3600)
    result.message.date = datetime.datetime.fromtimestamp(point.timestamp)
    return result


def create_tg_location_update(prev_update: MagicMock, point: db.TrackPoint, final_point=False):
    result = create_tg_update()

        result.message.chat.id = prev_update.message.chat.id
        result.message.chat.type = prev_update.message.chat.type
        result.message.chat.username = prev_update.message.chat.username
        result.message.chat.title = prev_update.message.chat.title

        result.message.message_id = prev_update.message.message_id
        result.message.from_user.id = prev_update.message.from_user.id
        result.message.from_user.first_name = prev_update.message.from_user.first_name

        result.message.location = create_tg_location(point.lat, point.lon, live_period=None if final_point else 3600)
        result.message.edit_date = datetime.datetime.fromtimestamp(point.timestamp)
        result.edited_message = result.message
        return result


@pytest.fixture
def mock_update_factory():
    return create_tg_update


@pytest.fixture
def mock_location_start_factory():
    return create_tg_start_update


@pytest.fixture
def mock_location_update_factory():
    return create_tg_location_update


@pytest.fixture
def mock_context():
    context = MagicMock(spec=telegram.ext.ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock(spec=telegram.Bot)
    return context


@pytest.fixture
def mock_location_factory():
    return create_tg_location
