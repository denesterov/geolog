import pytest
import geobot
import db
import test_utils
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
async def test_idling(mock_location_start_factory, mock_location_update_factory, mock_context):
    await cases_data.help_test_gpx_data(mock_context, cases_data.general_idling)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_speeding(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_point(45.24128, 19.84262, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [ # Speeding points
            test_utils.make_point(45.23612, 19.84651, "2025-05-11 21:45:50"), # 652.8 m (78.3 km/h)
            test_utils.make_point(45.23110, 19.85335, "2025-05-11 21:46:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_point(45.23076, 19.85294, "2025-05-11 21:46:50"), # 0.0 m (from speeding end)
            test_utils.make_point(45.23037, 19.85230, "2025-05-11 21:47:20"), # 66.2 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 5, 71.2 + 74.7 + 66.2, 60.0 + 30.0, {1})
    assert mock_context.bot.send_message.call_count == 2
