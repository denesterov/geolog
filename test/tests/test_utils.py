import datetime
import db
import geobot
import pytest


def create_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def make_track_point(lat, lon, date_str):
    return db.TrackPoint(lat, lon, create_datetime(date_str).timestamp())


def help_test_gpx_data(context, segments: list[list[db.TrackPoint]], skip_segments: set[int],
        exp_points_num: int, exp_length: float, exp_duration: float):

    start_upd = conftest.create_tg_start_update(segments[0][0])
    await geobot.cmd_message(start_upd, context)

    for segment in segments:
        for point in segment:
            final_point = point is segments[-1][-1]
            await geobot.cmd_message(conftest.create_tg_location_update(start_upd, point, final_point=final_point), context)

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
