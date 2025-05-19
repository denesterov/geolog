import datetime
import db
import geobot
import pytest


def create_datetime(date_str):
    return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")


def make_track_point(lat, lon, date_str):
    return db.TrackPoint(lat, lon, create_datetime(date_str).timestamp())


def help_test_gpx_data(sess_id:str, exp_segments: list[list[db.TrackPoint]], exp_length: float, exp_duration: float, skip_segments: set[int] = {}):
    info, segments = db.get_track(sess_id)
    gpx_data = geobot.create_gpx_data(segments)

    assert info.length == pytest.approx(exp_length, 1.0)
    assert info.duration == pytest.approx(exp_duration, 0.1)
    assert gpx_data is not None

    filtered_segments = [seg for i, seg in enumerate(exp_segments) if i not in skip_segments]
    exp_gpx_data = geobot.create_gpx_data(filtered_segments)

    assert gpx_data == exp_gpx_data
