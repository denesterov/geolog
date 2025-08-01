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
    assert sd.get_updates() == dict()
    assert len(pd.points) == 1


def test_smoke():
    tracker_test_utils.help_test_track(cases_data.smoke)

def test_short_idling():
    tracker_test_utils.help_test_track(cases_data.short_idling)

def test_general_idling():
    tracker_test_utils.help_test_track(cases_data.general_idling)

def test_speeding():
    tracker_test_utils.help_test_track(cases_data.speeding)

def test_speeding_then_idling():
    tracker_test_utils.help_test_track(cases_data.speeding_then_idling)

@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/20")
def test_idling_then_speeding():
    tracker_test_utils.help_test_track(cases_data.idling_then_speeding)

@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/22")
def test_right_away_speeding():
    tracker_test_utils.help_test_track(cases_data.right_away_speeding)

@pytest.mark.skip(reason="https://github.com/denesterov/geolog/issues/22")
def test_long_idling_then_speeding():
    tracker_test_utils.help_test_track(cases_data.long_idling_then_speeding)
