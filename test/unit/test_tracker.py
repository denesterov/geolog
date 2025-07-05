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
    tracker_test_utils.help_test_track(cases_data.smoke)
