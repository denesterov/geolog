import pytest
import tracker
import common
import cases_data

def get_default_sess_data(first_point:common.Point=None):
    fp = first_point if first_point is not None else common.Point(43.776122, 21.893356, 1749054111)

    data = tracker.new_session_data(87654321, 5678901, 345123, chat_type='PUB', chat_name='Kurilka', lat=fp.lat, long=fp.long, timestamp=fp.ts)
    data['id'] = 'c93840ba-8560-4a23-940f-0c23c45b8807'
    return data


def create_basic_env(first_point:common.Point=None, sess_data=None):
    sd = tracker.SessionData(sess_data if sess_data else get_default_sess_data(first_point))
    pd = tracker.PointsData()
    tr = tracker.Tracker(sd, pd)
    return (tr, sd, pd)


def help_test_track(cs: cases_data.Case):
    tr, sd, pd = create_basic_env(cs.track[0][0])

    for segm in cs.track:
        for pnt in segm:
            tr.update(pnt, location_is_new=pnt is cs.track[0][0])

    print(f'help_test_track. {sd.get_dirty_fields()=}')
    assert sd.get_dirty_fields() == cs.expected_dirty_fields

    print(f'help_test_track. {sd.length=}, {sd.duration=}, {len(pd.points)=}')
    assert sd.length == pytest.approx(cs.expect_length, 1.0)
    assert sd.duration == pytest.approx(cs.expect_duration, 0.1)
    assert len(pd.points) == cs.expect_gpx_points

    filtered_points = []
    for i, seg in enumerate(cs.track):
        if i in cs.skip_segments:
            continue
        filtered_points += [point for j, point in enumerate(seg) if (i, j) not in cs.skip_points]

    print(f'help_test_track. {pd.points=}')
    print(f'help_test_track. {filtered_points=}')
    assert len(pd.points) == len(filtered_points)

    for i, pnt in enumerate(filtered_points):
        assert pd.points[i] == pnt
