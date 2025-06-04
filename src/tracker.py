import telegram
from collections import namedtuple

Point = namedtuple('Point', ['lat', 'lon', 'timestamp'])

class SessionData:
    valid_data_fields = {
        'usr_id', 'chat_id', 'msg_id', 'chat_type', 'chat_name',
        'ts', 'length', 'duration', 'last_update',
        'last_lat', 'last_long', 'track_segm_idx', 'track_segm_len' }

    def __init__(self, session_data: dict):
        self.__dict__['session_data'] = session_data
        self.__dict__['dirty'] = set()

    def __getattr__(self, name):
        sess_data = self.__dict__['session_data']
        valid_data_fields = SessionData.__dict__['valid_data_fields']
        assert name in valid_data_fields
        if name in sess_data:
            return sess_data[name]
        raise AttributeError(f"SessionData object has no attribute '{name}'")

    def __setattr__(self, name, value):
        sess_data = self.__dict__['session_data']
        dirty = self.__dict__['dirty']
        sess_data[name] = value
        dirty.add(name)

    def get_dirty_fields(self):
        return self.__dict__['dirty']


class PointsData:
    def __init__(self):
        self.points = []

    def add_point(self, point: Point):
        self.points.append(point)


class Tracker:
    def __init__(self, session_data: SessionData, points: PointsData):
        self.session_data = session_data
        self.points = points

    def add_location(self, location: telegram.Location, new_location: bool = False):

        pass
