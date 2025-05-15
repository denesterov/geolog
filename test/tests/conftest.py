import pytest
import telegram
from unittest.mock import AsyncMock, MagicMock
import sys
from pathlib import Path

# Add src directory to Python path
src_path = str(Path(__file__).parent.parent.parent / 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)

import db

@pytest.fixture(autouse=True)
def setup_redis():
    """Setup Redis before each test and flush it after"""
    db.setup_redis()
    redis = db.get_redis()
    redis.flushall()
    yield redis
    redis.flushall()

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