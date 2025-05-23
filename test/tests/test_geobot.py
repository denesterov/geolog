import pytest
from unittest.mock import patch
import geobot
import db
import conftest
import test_utils


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
async def test_smoke(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23930, 19.84120, "2025-05-17 16:20:00"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-17 16:20:30"), # 156.0 m
            test_utils.make_track_point(45.24122, 19.84237, "2025-05-17 16:21:10"), # 74.7 m
        ],
    ]
    await test_utils.help_test_gpx_data(mock_context, track, 3, 156.0 + 74.7, 70.0)
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_idling(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23797, 19.84223, "2025-05-11 20:10:00"), # 0.0 m
            test_utils.make_track_point(45.23864, 19.84186, "2025-05-11 20:10:30"), # 79.7 m
            test_utils.make_track_point(45.23930, 19.84120, "2025-05-11 20:11:00"), # 89.3 m
        ],
        [ # Idling points
            test_utils.make_track_point(45.23935, 19.84125, "2025-05-11 20:11:30"),
            test_utils.make_track_point(45.23937, 19.84127, "2025-05-11 20:12:00"),
            test_utils.make_track_point(45.23939, 19.84129, "2025-05-11 20:13:00"),
            test_utils.make_track_point(45.23937, 19.84125, "2025-05-11 20:14:00"),
            test_utils.make_track_point(45.23935, 19.84127, "2025-05-11 20:14:45"),
        ],
        [
            test_utils.make_track_point(45.23996, 19.84185, "2025-05-11 20:15:00"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-11 20:15:30"), # 71.2 m
            test_utils.make_track_point(45.24122, 19.84237, "2025-05-11 20:16:00"), # 74.7 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 6, 79.7 + 89.0 + 71.2 + 74.7, 60.0 + 60.0, {1})
    assert mock_context.bot.send_message.call_count == 2


@pytest.mark.asyncio
async def test_speeding(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23996, 19.84185, "2025-05-11 21:44:20"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-11 21:44:50"), # 71.2 m
            test_utils.make_track_point(45.24128, 19.84262, "2025-05-11 21:45:20"), # 74.7 m
        ],
        [ # Speeding points
            test_utils.make_track_point(45.23612, 19.84651, "2025-05-11 21:45:50"), # 652.8 m (78.3 km/h)
            test_utils.make_track_point(45.23110, 19.85335, "2025-05-11 21:46:20"), # 774.0 m (92.9 km/h)
        ],
        [
            test_utils.make_track_point(45.23076, 19.85294, "2025-05-11 21:46:50"), # 0.0 m (from speeding end)
            test_utils.make_track_point(45.23037, 19.85230, "2025-05-11 21:47:20"), # 66.2 m
        ],
    ]

    await test_utils.help_test_gpx_data(mock_context, track, 5, 71.2 + 74.7 + 66.2, 60.0 + 30.0, {1})
    assert mock_context.bot.send_message.call_count == 2
