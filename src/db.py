import os
import logging
import redis
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import uuid
from geopy import distance
from collections import namedtuple

import const

DebugSession = namedtuple('DebugSession', ['id', 'ts', 'chat_name', 'points_num', 'length', 'duration'])

logger = logging.getLogger('geobot-db')

redis_db = None


# point = {
#   sess_id = "uuid",
#   usr_id = 100500,
#   ts = 441818433,
#   latitude = 33.3,
#   longitude = 55.5,
#   segm_id = 4,
# }
#
# session = {
#   usr_id = 100500,
#   chat_id = 100600,
#   msg_id = 100800,
#   chat_type = "PUB|PRIV"
#   chat_name = "EUC Tusovka"
#   ts = 441818433, # timestamp of the recording start, UTC
#   length = 953.4, # total recorded length in meters
#   duration = 580.0, # total duration in seconds
#   last_update = 100900, # last update timestamp
#   last_lat = 34.4, # last recorded point coordinates; to filter jitter and limit speed
#   last_long = 56.7,
#   track_segm_idx = 1, # current track segment id
#   track_segm_len = 5, # current track segment length, points
# }


def get_redis():
    global redis_db
    if redis_db is None:
        host = os.environ.get('REDIS_HOST')
        port = os.environ.get('REDIS_PORT')
        host = host if host is not None else 'localhost'
        port = port if port is not None else 6379
        logger.info(f'get_redis. host={host}, port={port}')
        redis_db = redis.Redis(host=host, port=port, db=0, decode_responses=True)
    # todo: Check connection state and reconnect if needed
    return redis_db


def setup_redis():
    r = get_redis()

    sess_index = r.ft('idx:session')
    try:
        sess_index.info()
    except:
        sess_index = None
    if sess_index is None:
        logger.info('Creating index for sessions')
        sess_index = r.ft('idx:session')
        sess_schema = (
            NumericField('usr_id'),
            NumericField('chat_id'),
            NumericField('msg_id'),
            NumericField('ts'),
        )
        sess_index.create_index(
            sess_schema,
            definition=IndexDefinition(prefix=['session:'], index_type=IndexType.HASH),
        )

    point_index = r.ft('idx:point')
    try:
        point_index.info()
    except:
        point_index = None
    if point_index is None:
        point_index = r.ft('idx:point')
        logger.info('Creating index for points')
        point_schema = (
            TagField('sess_id'),
            NumericField('ts'),
        )
        point_index.create_index(
            point_schema,
            definition=IndexDefinition(prefix=['point:'], index_type=IndexType.HASH),
        )

    logger.info('Redis is ready')


def get_or_create_session(usr_id, msg_id, tg_chat, loc, common_ts):
    r = get_redis()
    idx = r.ft('idx:session')
    res = idx.search(Query(f'@usr_id:[{usr_id} {usr_id}] @chat_id:[{tg_chat.id} {tg_chat.id}] @msg_id:[{msg_id} {msg_id}]'))
    logger.info(f'get_or_create_session. Session search: {res}')
    if res.total == 0:
        logger.info(f'Creating new session for usr_id={usr_id}')
        uid = f'session:{uuid.uuid1()}'
        session = {
            'usr_id' : usr_id,
            'chat_id' : tg_chat.id,
            'msg_id' : msg_id,
            'chat_type' : 'PRIV' if tg_chat.type == 'private' else 'PUB',
            'chat_name' : tg_chat.title if tg_chat.title is not None else (tg_chat.username if tg_chat.username is not None else '-'),
            'ts' : common_ts,
            'length' : 0.0,
            'duration' : 0.0,
            'last_update' : common_ts,
            'last_lat' : loc.latitude,
            'last_long' : loc.longitude,
            'track_segm_idx' : 1,
            'track_segm_len' : 0,
        }
        new_res = r.hset(uid, mapping=session)
        logger.info(f'get_or_create_session. New session. usr_id={usr_id}, uid={uid}, res={new_res}')
        session['id'] = uid
        return session
    else:
        assert res.total == 1
        doc = res.docs[0]
        logger.info(f'get_or_create_session. Found old session for usr_id={usr_id}, sess={doc}')
        return doc


# fixme split logic and db io
def update_session(sess_data, loc, common_ts):
    last_lat = float(sess_data['last_lat'])
    last_long = float(sess_data['last_long'])
    time_period = common_ts - float(sess_data['last_update'])
    delta = distance.distance((last_lat, last_long), (loc.latitude, loc.longitude)).m
    velocity = delta / time_period if time_period > 0.1 else 100.0 # todo: Do not record overspeed sections

    def finish_segment(sess_data):
        if int(sess_data['track_segm_len']) == 0:
            return None
        segm_id = int(sess_data['track_segm_idx'])
        logger.info(f'update_session. finishing segment. sess_id={sess_data["id"]}, segm_id={segm_id}')
        return {
            'track_segm_idx' : segm_id + 1,
            'track_segm_len' : 0,
            'last_update' : common_ts,
        }

    fields = None
    result = None
    if delta < const.MIN_GEO_DELTA:
        logger.info(f'update_session. skip coord update by idle. sess_id={sess_data["id"]}, delta={delta:.1f}, dt={time_period:.1f}') # todo: log debug
        if time_period > const.AFTER_PAUSE_TIME:
            fields = finish_segment(sess_data)
            pass
        result = False
    elif velocity > const.MAX_SPEED:
        logger.info(f'update_session. skip coord update by overspeed. sess_id={sess_data["id"]}, delta={delta:.1f}, vel={velocity:.1f}') # todo: log debug
        fields = finish_segment(sess_data)
        result = False
    else:
        logger.info(f'update_session. writing update. sess_id={sess_data["id"]}, delta={delta:.1f}, vel={velocity:.1f}') # todo: log debug
        fields = {
            'last_lat' : loc.latitude,
            'last_long' : loc.longitude,
            'length' : float(sess_data['length']) + delta,
            'duration' : float(sess_data['duration']) + (common_ts - float(sess_data['last_update'])),
            'last_update' : common_ts,
            'track_segm_len' : int(sess_data['track_segm_len']) + 1,
        }
        result = True

    if fields is not None:
        r = get_redis()
        fields['last_update'] = common_ts
        r.hset(sess_data['id'], mapping=fields)
    return result


def store_location(sess_data, usr_id, loc, common_ts):
    sess_id = sess_data['id']
    segm_id = sess_data['track_segm_idx']

    r = get_redis()
    uid = f'point:{uuid.uuid1()}'
    point = {
        'sess_id' : sess_id,
        'usr_id' : usr_id,
        'latitude' : loc.latitude,
        'longitude' : loc.longitude,
        'ts' : common_ts,
        'segm_id' : segm_id
    }
    r.hset(uid, mapping=point)
    logger.info(f'store_location. sess_id={sess_id}, usr_id={usr_id}')


def escape_for_exact_search(hash_id):
    escaped = hash_id.replace(':', '\\:').replace('-', '\\-')
    return f'{{{escaped}}}'


def get_sessions(usr_id: int, offset: int, page_size: int, count_points: bool):
    r = get_redis()
    sess_idx = r.ft('idx:session')
    point_idx = r.ft('idx:point') if count_points else None

    sess_q = Query(f'@usr_id:[{usr_id} {usr_id}]').sort_by('ts', asc=False).paging(offset, page_size)
    res = sess_idx.search(sess_q)
    logger.debug(f'get_sessions. total_sessions={res.total}')

    sessions = []
    for doc in res.docs:
        sess_id = doc.id
        total_points = 0
        if count_points:
            q = Query(f'@sess_id:{escape_for_exact_search(sess_id)}').dialect(2)
            pnt_res = point_idx.search(q)
            logger.debug(f'get_sessions. points={pnt_res.total}')
            total_points = pnt_res.total
        sessions.append(DebugSession(
            sess_id,
            float(doc.ts),
            doc.chat_name,
            total_points,
            round(float(doc.length), 1),
            round(float(doc.duration), 1)))
    return (sessions, res.total)


def get_track(sess_id: str):
    logger.info(f'get_track. sess_id={sess_id}')

    r = get_redis()
    sess_data = r.hgetall(sess_id)

    point_idx = r.ft('idx:point')
    offset = 0
    page_size = 100
    limit = 10000
    raw_points = []
    while True:
        q = Query(f'@sess_id:{escape_for_exact_search(sess_id)}').dialect(2).sort_by('ts', asc=True).paging(offset, page_size)
        pnt_res = point_idx.search(q)
        logger.info(f'get_track. points={len(pnt_res.docs)}, total={pnt_res.total}')
        raw_points += \
            [(float(pnt.latitude),
              float(pnt.longitude),
              round(float(pnt.ts), 1),
              pnt.segm_id if hasattr(pnt, 'segm_id') else 1)
                for pnt in pnt_res.docs]
        offset += page_size
        if offset >= pnt_res.total:
            break
        assert len(raw_points) <= limit

    by_segm_id = {}
    for pnt in raw_points:
        lat, lon, ts, segm_id = pnt
        points = None
        if segm_id in by_segm_id.keys():
            points = by_segm_id[segm_id]
        else:
            points = []
            by_segm_id[segm_id] = points
        points.append((lat, lon, ts))
    
    points = []
    for segm_id in sorted(by_segm_id.keys()):
        points.append(by_segm_id[segm_id])

    info = {
        'length' : float(sess_data['length']),
        'duration' : float(sess_data['duration']),
        'timestamp' : float(sess_data['ts']),
    }
    return info, points, len(raw_points)
