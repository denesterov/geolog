import pytest
from tracker import SessionData


def test_session_data_init():
    test_data = {'name': 'test', 'value': 123}
    sess = SessionData(test_data)
    assert sess.__dict__['session_data']['name'] == 'test'
    assert sess.__dict__['session_data']['value'] == 123
    assert sess.__dict__['dirty'] == set()


def test_session_data_get():
    test_data = {'name': 'test', 'value': 123}
    sess = SessionData(test_data)
    assert sess.name == 'test'
    assert sess.value == 123


def test_session_data_set():
    test_data = {'name': 'test'}
    sess = SessionData(test_data)
    assert sess.name == 'test'
    sess.name = 'abc'
    assert sess.name == 'abc'
    assert sess.get_dirty() == {'name'}


@pytest.mark.skip(reason="no way of currently testing this")
def test_session_data_getattr():
    test_data = {'name': 'test', 'value': 123}
    session = SessionData(test_data)
    assert session.name == 'test'
    assert session.value == 123


@pytest.mark.skip(reason="no way of currently testing this")
def test_session_data_invalid_attribute():
    test_data = {'name': 'test'}
    session = SessionData(test_data)
    with pytest.raises(KeyError):
        _ = session.nonexistent
