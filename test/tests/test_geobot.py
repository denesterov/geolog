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
async def test_smoke(mock_update_factory, mock_context, mock_location_factory):
    up1 = mock_update_factory()
    up1.message.location = mock_location_factory(45.2393, 19.8412)
    up1.message.date = create_datetime("2025-05-17 16:20:00")
    await geobot.cmd_message(up1, mock_context)
    
    up2 = mock_update_factory()
    up2.message.location = mock_location_factory(45.24060, 19.84200)
    up2.message.edit_date = create_datetime("2025-05-17 16:20:30")
    up2.edited_message = up2.message
    await geobot.cmd_message(up2, mock_context)

    up3 = mock_update_factory()
    up3.message.location = mock_location_factory(45.24122, 19.84237)
    up3.message.edit_date = create_datetime("2025-05-17 16:21:10")
    up3.edited_message = up3.message
    await geobot.cmd_message(up3, mock_context)
    
    sessions, total = db.get_sessions(up1.effective_user.id, 0, 10, True)
    assert total == 1
    assert len(sessions) == 1
    assert mock_context.bot.send_message.call_count == 1
    assert sessions[0].points_num == 3
    assert sessions[0].length == pytest.approx(229.0, 0.5)
    assert sessions[0].duration == pytest.approx(70.0, 0.01)
