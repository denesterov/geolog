import pytest
import geobot
import db
import cases_data


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
async def test_smoke(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.smoke)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_short_idling(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.short_idling)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_idling(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.general_idling)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_speeding(mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.speeding)
    assert mock_context.bot.send_message.call_count == 2
