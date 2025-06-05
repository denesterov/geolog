import pytest
import tracker


def get_default_sess_data():
    return {
        'id': 'c93840ba-8560-4a23-940f-0c23c45b8807',
        'usr_id': 87654321,
        'chat_id' : 5678901,
        'msg_id' : 345123,
        'chat_type' : 'PUB',
        'chat_name' : 'Kurilka',
        'ts' : 1749054111,
        'length' : 0.0,
        'duration' : 0.0,
        'last_update' : 1749054111,
        'last_lat' : 43.776122,
        'last_long' : 21.893356,
        'track_segm_idx' : 1,
        'track_segm_len' : 0,
    }


def create_basic_env(sess_data=None):
    sd = tracker.SessionData(sess_data if sess_data else get_default_sess_data())
    pd = tracker.PointsData()
    tr = tracker.Tracker(sd, pd)
    return (tr, sd, pd)
