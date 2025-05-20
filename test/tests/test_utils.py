import datetime
import db
import geobot
import pytest


def create_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def make_track_point(lat, lon, date_str):
    return db.TrackPoint(lat, lon, create_datetime(date_str).timestamp())


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


async def help_test_gpx_data(context, segments: list[list[db.TrackPoint]], skip_segments: set[int],
        exp_points_num: int, exp_length: float, exp_duration: float):

    start_upd = create_tg_start_update(segments[0][0])
    await geobot.cmd_message(start_upd, context)

    for segment in segments:
        for point in segment:
            final_point = point is segments[-1][-1]
            await geobot.cmd_message(create_tg_location_update(start_upd, point, final_point=final_point), context)

    sessions, total = db.get_sessions(start_upd.effective_user.id, 0, 10, True)
    assert total == 1
    assert len(sessions) == 1
    assert sessions[0].points_num == exp_points_num

    info, segments = db.get_track(sessions[0].id)
    gpx_data = geobot.create_gpx_data(segments)

    assert info.length == pytest.approx(exp_length, 1.0)
    assert info.duration == pytest.approx(exp_duration, 0.1)
    assert gpx_data is not None

    filtered_segments = [seg for i, seg in enumerate(exp_segments) if i not in skip_segments]
    exp_gpx_data = geobot.create_gpx_data(filtered_segments)

    assert gpx_data == exp_gpx_data
