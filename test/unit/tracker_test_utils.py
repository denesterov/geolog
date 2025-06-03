import pytest
import tracker


def get_default_sess_data(first_point:tracker.Point=None):
    fp = first_point if first_point is not None else tracker.Point(43.776122, 21.893356, 1749054111)

    data = tracker.new_session_data(87654321, 5678901, 345123, chat_type='PUB', chat_name='Kurilka', lat=fp.lat, long=fp.long, timestamp=fp.ts)
    data['id'] = 'c93840ba-8560-4a23-940f-0c23c45b8807'
    return data


def create_basic_env(first_point:tracker.Point=None, sess_data=None):
    sd = tracker.SessionData(sess_data if sess_data else get_default_sess_data(first_point))
    pd = tracker.PointsData()
    tr = tracker.Tracker(sd, pd)
    return (tr, sd, pd)
