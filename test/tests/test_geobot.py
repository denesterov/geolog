import pytest
from unittest.mock import patch
import geobot
import db

@pytest.mark.asyncio
async def test_cmd_message_new_location(mock_update, mock_context, mock_location):
    """Test handling of a new location message"""
    # Set up the mock location message
    mock_update.message.location = mock_location
    
    # Call the command handler
    await geobot.cmd_message(mock_update, mock_context)
    
    # Verify that a new session was created
    sessions, total = db.get_sessions(mock_update.effective_user.id, 0, 10, True)
    assert total == 1
    assert len(sessions) == 1
    
    session = sessions[0]
    assert session.timestamp == mock_update.message.date.timestamp()
    assert session.chat_name == "test_user"
    
    # Verify that the bot sent a confirmation message
    mock_context.bot.send_message.assert_called_once_with(
        chat_id=mock_update.effective_chat.id,
        text="Test User started location recording."
    )

@pytest.mark.asyncio
async def test_cmd_message_edited_location(mock_update, mock_context, mock_location):
    """Test handling of an edited location message"""
    # First create a session with initial location
    mock_update.message.location = mock_location
    await geobot.cmd_message(mock_update, mock_context)
    
    # Now simulate an edited location
    mock_update.edited_message = mock_update.message
    mock_update.message = None
    mock_location.latitude = 55.7560  # Slightly different coordinates
    mock_location.longitude = 37.6175
    mock_update.edited_message.location = mock_location
    mock_update.edited_message.edit_date = mock_update.edited_message.date
    
    # Call the command handler for edited message
    await geobot.cmd_message(mock_update, mock_context)
    
    # Verify that we still have one session
    sessions, total = db.get_sessions(mock_update.effective_user.id, 0, 10, True)
    assert total == 1
    
    # Verify that no new confirmation message was sent
    assert mock_context.bot.send_message.call_count == 1  # Only from the first call

@pytest.mark.asyncio
async def test_cmd_message_static_location(mock_update, mock_context, mock_location):
    """Test handling of a static location message"""
    # Set up static location (no live_period)
    mock_location.live_period = None
    mock_update.message.location = mock_location
    
    # Call the command handler
    await geobot.cmd_message(mock_update, mock_context)
    
    # Verify that no session was created
    sessions, total = db.get_sessions(mock_update.effective_user.id, 0, 10, True)
    assert total == 0
    
    # Verify that no message was sent
    mock_context.bot.send_message.assert_not_called() 