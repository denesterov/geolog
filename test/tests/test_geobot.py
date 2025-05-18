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

    up1 = mock_location_start_factory(track[0][0])
    await geobot.cmd_message(up1, mock_context)
    await geobot.cmd_message(mock_location_update_factory(up1, track[0][1]), mock_context)
    await geobot.cmd_message(mock_location_update_factory(up1, track[0][2], final_point=True), mock_context)
    
    sessions, total = db.get_sessions(up1.effective_user.id, 0, 10, True)
    assert total == 1
    assert len(sessions) == 1
    assert mock_context.bot.send_message.call_count == 2
    assert sessions[0].points_num == 3

    test_utils.help_test_gpx_data(sessions[0].id, track, 156.0 + 74.7, 70.0)


@pytest.mark.asyncio
async def test_idling(mock_location_start_factory, mock_location_update_factory, mock_context):
    track = [
        [
            test_utils.make_track_point(45.23797, 19.84223, "2025-05-11 20:10:00"), # 0.0 m
            test_utils.make_track_point(45.23864, 19.84186, "2025-05-11 20:10:30"), # 79.7 m
            test_utils.make_track_point(45.23930, 19.84120, "2025-05-11 20:11:00"), # 89.3 m
        ],
        [
            test_utils.make_track_point(45.23996, 19.84185, "2025-05-11 20:15:00"), # 0.0 m
            test_utils.make_track_point(45.24060, 19.84200, "2025-05-11 20:15:30"), # 71.2 m
            test_utils.make_track_point(45.24122, 19.84237, "2025-05-11 20:16:00"), # 74.7 m
        ],
    ]

    idle = [
        test_utils.make_track_point(45.23935, 19.84125, "2025-05-11 20:11:30"),
        test_utils.make_track_point(45.23937, 19.84127, "2025-05-11 20:12:00"),
        test_utils.make_track_point(45.23939, 19.84129, "2025-05-11 20:13:00"),
        test_utils.make_track_point(45.23937, 19.84125, "2025-05-11 20:14:00"),
        test_utils.make_track_point(45.23935, 19.84127, "2025-05-11 20:14:45"),
    ]

    up1 = mock_location_start_factory(track[0][0])
    await geobot.cmd_message(up1, mock_context)
    for point in track[0][1:]:
        await geobot.cmd_message(mock_location_update_factory(up1, point), mock_context)
    for point in idle:
        await geobot.cmd_message(mock_location_update_factory(up1, point), mock_context)
    for point in track[1]:
        await geobot.cmd_message(mock_location_update_factory(up1, point, final_point=point is track[1][-1]), mock_context)

    sessions, total = db.get_sessions(up1.effective_user.id, 0, 10, True)
    assert total == 1
    assert len(sessions) == 1
    assert mock_context.bot.send_message.call_count == 2
    assert sessions[0].points_num == 6

    test_utils.help_test_gpx_data(sessions[0].id, track, 79.7 + 89.0 + 71.2 + 74.7, 60.0 + 60.0)
