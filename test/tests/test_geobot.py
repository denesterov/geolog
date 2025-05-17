import pytest
from unittest.mock import patch
import geobot
import db
import conftest


@pytest.mark.asyncio
async def test_new_session(mock_update_factory, mock_context, mock_location_factory):
    update = mock_update_factory()
    update.message.location = mock_location_factory()

    await geobot.cmd_message(update, mock_context)

    sessions, total = db.get_sessions(update.effective_user.id, 0, 10, True)
    assert total == 1
    assert len(sessions) == 1
    
    session = sessions[0]
    assert session.timestamp == update.message.date.timestamp()
    assert session.chat_name == "test_user"

    mock_context.bot.send_message.assert_called_once_with(
        chat_id=update.effective_chat.id,
        text="Test User started location recording."
    )


@pytest.mark.asyncio
async def test_static_location(mock_update_factory, mock_context, mock_location_factory):
    update = mock_update_factory()
    update.message.location = mock_location_factory(live_period=None)

    await geobot.cmd_message(update, mock_context)

    sessions, total = db.get_sessions(update.effective_user.id, 0, 10, True)
    assert total == 0
    
    mock_context.bot.send_message.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.skip
async def test_cmd_message_edited_location(mock_update_factory, mock_context, mock_location_factory):
    """Test handling of an edited location message"""
    # First create a session with initial location
    update = mock_update_factory()
    update.message.location = mock_location_factory()
    await geobot.cmd_message(update, mock_context)
    
    # Now simulate an edited location
    update.edited_message = update.message
    update.message = None
    update.edited_message.location = mock_location_factory()
    update.edited_message.edit_date = update.edited_message.date
    
    # Call the command handler for edited message
    await geobot.cmd_message(update, mock_context)
    
    # Verify that we still have one session
    sessions, total = db.get_sessions(update.effective_user.id, 0, 10, True)
    assert total == 1
    
    # Verify that no new confirmation message was sent
    assert mock_context.bot.send_message.call_count == 1  # Only from the first call
