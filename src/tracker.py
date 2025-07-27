# import telegram
import const
import common
from geopy import distance
import logging

logger = logging.getLogger('tracker')


def new_session_data(usr_id, chat_id, msg_id, chat_type='PRIV', chat_name='', lat=0.0, long=0.0, timestamp=0):
    return {
        'usr_id': usr_id,
        'chat_id': chat_id,
        'msg_id': msg_id,
        'chat_type': chat_type,
        'chat_name' : chat_name,
        'ts' : timestamp,
        'length' : 0.0,
        'duration' : 0.0,
        'last_update' : timestamp,
        'last_lat' : lat,
        'last_long' : long,
        'track_segm_idx' : 1,
        'track_segm_len' : 1, # We assume that for a new session, the first point will be stored immediately
    }


def new_session_data_ex(usr_id, msg_id, tg_chat, loc, timestamp):
    return new_session_data(usr_id, tg_chat.id, msg_id,
        chat_type='PRIV' if tg_chat.type == 'private' else 'PUB',
        chat_name=tg_chat.title if tg_chat.title is not None else (tg_chat.username if tg_chat.username is not None else '-'),
        lat=loc.latitude, long=loc.longitude, timestamp=timestamp)


class SessionData:
    valid_data_fields = set(new_session_data(1, 1, 1).keys()) | {'id'}
    int_fields = {'track_segm_idx', 'track_segm_len'}
    float_fields = {'ts', 'length', 'duration', 'last_update', 'last_lat', 'last_long'}

    def __init__(self, session_data: dict):
        self.__dict__['session_data'] = session_data
        self.__dict__['dirty'] = set()

    def __getattr__(self, name):
        sess_data = self.__dict__['session_data']
        valid_data_fields = SessionData.__dict__['valid_data_fields']
        int_flds = SessionData.__dict__['int_fields']
        flt_flds = SessionData.__dict__['float_fields']

        logger.info(f'SessionData.__getattr__. {name=}, {type(name)=}, {sess_data=}, {valid_data_fields=}') # debug

        assert name in valid_data_fields

        value = None
        if isinstance(sess_data, dict) and name in sess_data.keys():
            value = sess_data[name]
        else:
            value = getattr(sess_data, name, None)

        if value is not None:
            if name in int_flds:
                value = int(value)
            elif name in flt_flds:
                value = float(value)
            return value
        raise AttributeError(f"SessionData object has no attribute '{name}'")

    def __setattr__(self, name, value):
        sess_data = self.__dict__['session_data']
        dirty = self.__dict__['dirty']
        sess_data[name] = value
        dirty.add(name)

    def __getitem__(self, item):
        value = getattr(self, item)
        return value

    def get_dirty_fields(self):
        return self.__dict__['dirty']



class PointsData:
    def __init__(self):
        self.points = []

    def add(self, point: common.Point):
        self.points.append(point)



class Tracker:
    def __init__(self, session_data: SessionData, points: PointsData):
        self.session = session_data
        self.points = points


    def finish_segment(self):
        segm_len = self.session.track_segm_len
        if segm_len == 0:
            return
        segm_id = self.session.track_segm_idx
        logger.info(f'finish_segment. sess_id={self.session.id}, {segm_id=}, {segm_len=}')
        self.session.track_segm_idx = segm_id + 1
        self.session.track_segm_len = 0


    def update_last_location(self, location: common.Point):
        self.session.last_lat = location.latitude
        self.session.last_long = location.longitude
        self.session.last_update = location.ts


    def update(self, location: common.Point, location_is_new: bool = False):
        if location_is_new:
            self.points.add(location)
            return

        sess_id = self.session.id
        segm_len = self.session.track_segm_len
        timestamp = location.ts

        time_period = timestamp - self.session.last_update
        delta = distance.distance((self.session.last_lat, self.session.last_long), (location.latitude, location.longitude)).m
        velocity = delta / time_period if time_period > 0.1 else 0.0

        if delta < const.MIN_GEO_DELTA:
            logger.info(f'update. skip coord update by idle. {sess_id=}, {delta=:.1f}, dt={time_period:.1f}') # todo: log debug
            if time_period > const.AFTER_PAUSE_TIME:
                self.finish_segment()
                self.session.last_update = timestamp
        elif velocity > const.MAX_SPEED:
            logger.info(f'update. skip coord update by overspeed. {sess_id=}, {delta=:.1f}, {velocity=:.1f}') # todo: log debug
            self.finish_segment()
            self.update_last_location(location)
        else:
            logger.info(f'update. writing update. {sess_id=}, {segm_len=}, {delta=:.1f}, {velocity=:.1f}, dt={time_period:.1f}') # todo: log debug
            self.update_last_location(location)
            if segm_len > 0:
                self.session.length = self.session.length + delta
                self.session.duration = self.session.duration + time_period
            self.session.track_segm_len = segm_len + 1
            self.points.add(location)
