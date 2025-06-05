import pytest
import tracker
import tracker_test_utils


def test_creation():
    tr, sd, pd = tracker_test_utils.create_basic_env()
    assert tr.session.usr_id == 87654321
    assert tr.session.chat_type == 'PUB'


def test_new_session():
    p = tracker.Point(45.2393, 19.8412, 100500)
    tr, sd, pd = tracker_test_utils.create_basic_env(p)
    tr.update(p, location_is_new=True)
    assert sd.get_dirty_fields() == set() #{'track_segm_len', 'last_lat', 'last_long', 'last_update', 'length', 'duration'}
    assert len(pd.points) == 1


def test_smoke():
    fp = tracker.Point(45.23930, 19.84120, 100500)
    tr, sd, pd = tracker_test_utils.create_basic_env(fp)

    tr.update(fp, location_is_new=True) # 0.0 m
    tr.update(tracker.Point(45.24060, 19.84200, 100530)) # 156.0 m
    tr.update(tracker.Point(45.24122, 19.84237, 100570)) # 74.7 m

    assert sd.get_dirty_fields() == {'track_segm_len', 'last_lat', 'last_long', 'last_update', 'length', 'duration'}
    print(f'SESSION LENGTH={sd.length}, DURATION={sd.duration}')
    assert sd.length == pytest.approx(156.0 + 74.7, 1.0)
    assert sd.duration == 70.0
    assert len(pd.points) == 3
    assert pd.points[0] == tracker.Point(45.23930, 19.84120, 100500)
    assert pd.points[1] == tracker.Point(45.24060, 19.84200, 100530)
    assert pd.points[2] == tracker.Point(45.24122, 19.84237, 100570)
