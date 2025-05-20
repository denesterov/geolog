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


@pytest.fixture
def mock_context():
    context = MagicMock(spec=telegram.ext.ContextTypes.DEFAULT_TYPE)
    context.bot = AsyncMock(spec=telegram.Bot)
    return context


@pytest.fixture
def mock_update_factory():
    return test_utils.create_tg_update


@pytest.fixture
def mock_location_start_factory():
    return test_utils.create_tg_start_update


@pytest.fixture
def mock_location_update_factory():
    return test_utils.create_tg_location_update


@pytest.fixture
def mock_location_factory():
    return test_utils.create_tg_location
