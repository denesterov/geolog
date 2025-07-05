import pytest
import tracker
import common


def test_session_data_init():
    test_data = {'chat_name': 'test', 'usr_id': 123}
    sess = tracker.SessionData(test_data)
    assert sess.__dict__['session_data']['chat_name'] == 'test'
    assert sess.__dict__['session_data']['usr_id'] == 123
    assert sess.__dict__['dirty'] == set()


def test_session_data_get():
    test_data = {'chat_name': 'test', 'usr_id': 123}
    sess = tracker.SessionData(test_data)
    assert sess.chat_name == 'test'
    assert sess.usr_id == 123


def test_session_data_set():
    test_data = {'chat_name': 'test', 'id': 5}
    sess = tracker.SessionData(test_data)
    assert sess.id == 5
    assert sess.chat_name == 'test'
    sess.chat_name = 'abc'
    assert sess.chat_name == 'abc'
    assert sess.get_dirty_fields() == {'chat_name'}
    sess.id = 6
    assert sess.id == 6
    assert sess.get_dirty_fields() == {'id', 'chat_name'}


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
