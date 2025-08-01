import pytest
import tracker
import common


def test_session_data_init():
    test_data = {'chat_name': 'test', 'usr_id': 123}
    sess = tracker.SessionData(test_data)
    assert sess.__dict__['data']['chat_name'] == 'test'
    assert sess.__dict__['data']['usr_id'] == 123
    assert sess.__dict__['updates'] == dict()


def test_session_data_get():
    test_data = {'chat_name': 'test', 'usr_id': 123}
    sess = tracker.SessionData(test_data)
    assert sess.chat_name == 'test'
    assert sess.usr_id == 123


def test_session_data_getitem():
    test_data = {'chat_name': 'test', 'usr_id': 123}
    sess = tracker.SessionData(test_data)
    assert sess['chat_name'] == 'test'
    assert sess['usr_id'] == 123


def test_session_data_set():
    test_data = {'chat_name': 'test', 'id': 5}
    sess = tracker.SessionData(test_data)
    assert sess.id == 5
    assert sess.chat_name == 'test'
    sess.chat_name = 'abc'
    assert sess.chat_name == 'abc'
    assert sess.get_updates() == {'chat_name': 'abc'}
    sess.id = 6
    assert sess.id == 6
    assert sess.get_updates() == {'id': 6, 'chat_name': 'abc'}


def test_type_conversion():
    sess = tracker.SessionData({'track_segm_len': 10, 'duration': 77.0})
    assert sess.track_segm_len == 10
    assert sess.duration == 77.0
    sess.track_segm_len = '12'
    assert sess.track_segm_len == 12
    assert sess.get_updates() == {'track_segm_len': '12'}
    sess.duration = '88.0'
    assert sess.duration == 88.0
    assert sess.get_updates() == {'track_segm_len': '12', 'duration': '88.0'}


def test_session_data_invalid_attribute():
    test_data = {'chat_name': 'test'}
    session = tracker.SessionData(test_data)
    with pytest.raises(AssertionError):
        _ = session.nonexistent


def test_points_data():
    data = tracker.PointsData()
    assert data.points == []
    data.add(common.Point(33.44, 55.66, 1749053938))
    assert data.points == [common.Point(33.44, 55.66, 1749053938)]
