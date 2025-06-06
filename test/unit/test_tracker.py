import pytest
import common
import tracker_test_utils
import cases_data


def test_creation():
    tr, sd, pd = tracker_test_utils.create_basic_env()
    assert tr.session.usr_id == 87654321
    assert tr.session.chat_type == 'PUB'


def test_new_session():
    p = common.Point(45.2393, 19.8412, 100500)
    tr, sd, pd = tracker_test_utils.create_basic_env(p)
    tr.update(p, location_is_new=True)
    assert sd.get_dirty_fields() == set()
    assert len(pd.points) == 1


def test_smoke():
    c = cases_data.smoke

    tr, sd, pd = tracker_test_utils.create_basic_env(c.track[0][0])

    tr.update(c.track[0][0], location_is_new=True)
    tr.update(c.track[0][1])
    tr.update(c.track[0][2])

    assert sd.get_dirty_fields() == {'track_segm_len', 'last_lat', 'last_long', 'last_update', 'length', 'duration'}
    print(f'SESSION LENGTH={sd.length}, DURATION={sd.duration}')
    assert sd.length == pytest.approx(156.0 + 74.7, 1.0)
    assert sd.duration == 70.0
    assert len(pd.points) == 3
    assert pd.points[0] == c.track[0][0]
    assert pd.points[1] == c.track[0][1]
    assert pd.points[2] == c.track[0][2]
