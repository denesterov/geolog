import os
import math
import logging
import redis
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import uuid
import time
import datetime
import telegram
import telegram.ext
import gpx
from geopy import distance


logger = None
redis_db = None

def db_get_redis():
    global redis_db
    if redis_db is None:
        host = os.environ.get('REDIS_HOST')
        port = os.environ.get('REDIS_PORT')
        host = host if host is not None else 'localhost'
        port = port if port is not None else 6379
        logger.info(f'db_get_redis. host={host}, port={port}')
        redis_db = redis.Redis(host=host, port=port, db=0, decode_responses=True)
    # todo: Check connection state and reconnect if needed
    return redis_db


# point = {
#   sess_id = "uuid",
#   usr_id = 100500,
#   ts = 441818433,
#   latitude = 33.3,
#   longitude = 55.5,
# }
#
# session = {
#   usr_id = 100500,
#   chat_id = 100600,
#   msg_id = 100800,
#   chat_type = "PUB|PRIV"
#   chat_name = "EUC Tusovka"
#   ts = 441818433,
#   length = 953.4,
#   duration = 580.0,
#   last_update = 100900
#   last_lat = 34.4
#   last_long = 56.7
# }

def db_setup_redis():
    r = db_get_redis()

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


def db_get_session(usr_id, msg_id, tg_chat, loc, common_ts):
    r = db_get_redis()
    idx = r.ft('idx:session')
    res = idx.search(Query(f'@usr_id:[{usr_id} {usr_id}] @chat_id:[{tg_chat.id} {tg_chat.id}] @msg_id:[{msg_id} {msg_id}]'))
    logger.info(f'Session search:{res}')
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
        }
        new_res = r.hset(uid, mapping=session)
        logger.info(f'New session. usr_id={usr_id}, uid={uid}, res={new_res}')
        session['id'] = uid
        return session
    else:
        assert res.total == 1
        doc = res.docs[0]
        logger.info(f'Found old session for usr_id={usr_id}, sess={doc}')
        return doc


def db_update_session(sess_data, loc, common_ts):
    do_store_point = True
    fields = {}

    last_lat = float(sess_data['last_lat'])
    last_long = float(sess_data['last_long'])
    delta = distance.distance((last_lat, last_long), (loc.latitude, loc.longitude)).m
    if delta < 20.0:
        logger.info(f'db_update_session. skip update by delta. sess_id={sess_data["id"]}, delta={delta:.1f}')
        do_store_point = False
    else:
        fields['last_lat'] = loc.latitude
        fields['last_long'] = loc.longitude
        fields['length'] = float(sess_data['length']) + delta
        fields['duration'] = float(sess_data['duration']) + (common_ts - float(sess_data['last_update']))
        fields['last_update'] = common_ts

    r = db_get_redis()
    r.hset(sess_data['id'], mapping=fields)
    return do_store_point


def db_store_location(sess_id, usr_id, loc, common_ts):
    r = db_get_redis()
    uid = f'point:{uuid.uuid1()}'
    point = {
        'sess_id' : sess_id,
        'usr_id' : usr_id,
        'latitude' : loc.latitude,
        'longitude' : loc.longitude,
        'ts' : common_ts,
    }
    r.hset(uid, mapping=point)
    logger.info(f'Location stored. sess_id={sess_id}, usr_id={usr_id}')


def db_get_track(sess_id: str):
    logger.info(f'db_get_track. sess_id={sess_id}')

    r = db_get_redis()
    sess_data = r.hgetall(sess_id)

    point_idx = r.ft('idx:point')
    offset = 0
    page_size = 100
    limit = 10000
    points = []
    while True:
        q = Query(f'@sess_id:{db_escape_for_exact_search(sess_id)}').dialect(2).sort_by('ts', asc=True).paging(offset, page_size)
        pnt_res = point_idx.search(q)
        logger.info(f'db_get_track. points={len(pnt_res.docs)}, total={pnt_res.total}')
        for pnt in pnt_res.docs:
            points.append((float(pnt.latitude), float(pnt.longitude), round(float(pnt.ts), 1)))
        offset += page_size
        if offset >= pnt_res.total:
            break
        assert len(points) <= limit

    info = {
        'length' : float(sess_data['length']),
        'duration' : float(sess_data['duration']),
        'timestamp' : float(sess_data['ts']),
    }
    return info, points


async def cmd_message(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    msg = None
    new_location = None

    if update.edited_message is not None and update.edited_message.location is not None:
        msg = update.edited_message
        new_location = False
    elif update.message is not None and update.message.location is not None:
        if update.message.location.live_period is None:
            logger.info(f'Static location received. Ignoring. chat_id={update.message.chat.id}, msg_id={update.message.message_id}, usr_id={update.message.from_user.id}')
        else:
            msg = update.message
            new_location = True

    if msg is not None:
        logger.info(f'Location: new={new_location}, chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}, chat_type={msg.chat.type}, loc={msg.location}')
        dt = msg.edit_date if msg.edit_date is not None else msg.date
        common_ts = dt.timestamp() if dt else time.time()
        sess_data = db_get_session(msg.from_user.id, msg.message_id, msg.chat, msg.location, common_ts)
        sess_id = sess_data['id']
        if new_location or db_update_session(sess_data, msg.location, common_ts):
            db_store_location(sess_id, msg.from_user.id, msg.location, common_ts)

        usr_name = update.effective_user.first_name if update.effective_user else 'User'
        if (new_location):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usr_name} started location recording.')
        elif msg.location.live_period is None:
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usr_name} stopped location recording.')


def db_escape_for_exact_search(hash_id):
    escaped = hash_id.replace(':', '\\:').replace('-', '\\-')
    return f'{{{escaped}}}'


def duration_to_human(dur: float):
    days = int(dur / 86400)
    days_rem = math.fmod(dur, 86400)
    hours = int(days_rem / 3600)
    hours_rem = math.fmod(days_rem, 3600)
    mins = int(hours_rem / 60)
    result = (f'{days} days ' if days > 0 else '')
    result += (f'{hours} hours' if hours > 0 or days > 0 else '')
    result += (' ' if hours > 0 and days == 0 else '')
    result += (f'{mins} minutes' if days == 0 else '')
    return result


def create_gpx_data(points):
    gpx_inst = gpx.GPX()
    gpx_inst.name = 'Telegram GPS track'
    gpx_inst.creator='Geograph'
    gpx_inst.descr = 'This GPX file was created by Geograph Telegram Bot'
    gpx_inst.tracks.append(gpx.track.Track())
    gpx_inst.tracks[0].segments.append(gpx.track_segment.TrackSegment())
    segment = gpx_inst.tracks[0].segments[0]

    for (lat, long, ts) in points:
        wp = gpx.Waypoint()
        wp.lat = lat
        wp.lon = long
        wp.time = datetime.datetime.fromtimestamp(ts)
        segment.append(wp)
    
    return gpx_inst.to_string()


def sessions_menu_item(sess_id: str):
    logger.info(f'sessions_menu_item. sess_id={sess_id}')

    info, points = db_get_track(sess_id)

    gpx_data = create_gpx_data(points)

    sess_len = info['length'] / 1000.0
    sess_dur = info['duration']

    ts_str = time.asctime(time.gmtime(info['timestamp']))
    descr = f'Here is your GPX file\n{ts_str} UTC\nLength {sess_len:.1f} km, duration {duration_to_human(sess_dur)}, {len(points)} points'

    sess_tm = datetime.datetime.fromtimestamp(info['timestamp'])
    file_name = f'TelegramTrack_{sess_tm.year}{sess_tm.month:02}{sess_tm.day:02}_{sess_tm.hour:02}{sess_tm.minute:02}.gpx'

    return (descr, telegram.InputFile(gpx_data, file_name))


def sessions_menu_create(usr_id: int, offset: int, page: int):
    logger.info(f'create_sessions_menu. offset={offset}, page={page}')

    r = db_get_redis()
    sess_idx = r.ft('idx:session')
    sess_q = Query(f'@usr_id:[{usr_id} {usr_id}]').sort_by('ts', asc=False).paging(offset, page)
    res = sess_idx.search(sess_q)
    logger.info(f'create_sessions_menu. session data. len={res.total}')

    keyboard = []
    for doc in res.docs:
        sess_id = doc.id
        length = float(doc.length) / 1000.0
        age = time.time() - float(doc.ts)
        descr = f'{duration_to_human(age)} ago, {length:.1f} km'
        keyboard.append([telegram.InlineKeyboardButton(descr, callback_data=f'session_menu_item {sess_id}')])

    navig_butts = []
    if offset >= page:
        navig_butts.append(telegram.InlineKeyboardButton('Prev', callback_data=f'session_menu {offset - page} {page}'))
    if len(res.docs) >= page:
        navig_butts.append(telegram.InlineKeyboardButton('Next', callback_data=f'session_menu {offset + page} {page}'))
    navig_butts.append(telegram.InlineKeyboardButton('Cancel', callback_data=f'session_cancel'))
    keyboard.append(navig_butts)

    return (f'Records from {offset} to {min(offset + page, res.total)} of {res.total}', telegram.InlineKeyboardMarkup(keyboard))


async def cmd_tracks(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    usr_id = update.effective_user.id
    logger.info(f'cmd_tracks. usr_id={usr_id}')
    menu_text, menu = sessions_menu_create(usr_id, 0, 5)
    await update.message.reply_text(menu_text, reply_markup=menu)


bot_start_time = time.monotonic()
async def cmd_debug_ping(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    uptime = time.monotonic() - bot_start_time
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Bot is alive! Uptime is {uptime / 3600.0:.1f} hours')


async def cmd_debug_tracks(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    usr_id = update.effective_user.id
    logger.info(f'cmd_debug_tracks. usr_id={usr_id}')
    r = db_get_redis()
    sess_idx = r.ft('idx:session')
    point_idx = r.ft('idx:point')

    sess_q = Query(f'@usr_id:[{usr_id} {usr_id}]').sort_by('ts', asc=False)
    res = sess_idx.search(sess_q)
    logger.info(f'cmd_debug_tracks. sessions_found={res.total}')

    lines = [f'Hello {update.effective_user.first_name} here is your tracks:\n\n']
    for doc in res.docs:
        sess_id = doc.id
        q = f'@sess_id:{db_escape_for_exact_search(sess_id)}'
        logger.info(f'cmd_debug_tracks. query={q}')
        pnt_res = point_idx.search(Query(q).dialect(2))
        logger.info(f'cmd_debug_tracks. points={pnt_res.total}')
        ts = float(doc.ts)
        tm = time.asctime(time.gmtime(ts))
        lines.append(f'Track: {sess_id}\n{tm}\nChat: {doc.chat_name}\nLength {round(float(doc.length), 1)} m, duration {doc.duration} s, {pnt_res.total} points\n\n')
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(lines))


async def cmd_button(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    data = query.data.split(' ')
    if data[0] == 'session_menu_item':
        descr, gpx_file = sessions_menu_item(data[1])
        await query.edit_message_text(text=descr)
        await context.bot.send_document(update.effective_chat.id, gpx_file)
    elif data[0] == 'session_menu':
        usr_id = update.effective_user.id
        logger.info(f'cmd_button. session_menu. usr_id={usr_id}')
        menu_text, menu = sessions_menu_create(usr_id, int(data[1]), int(data[2]))
        await query.edit_message_text(text=menu_text, reply_markup=menu)
    elif data[0] == 'session_cancel':
        await context.bot.deleteMessage(message_id = update.effective_message.id, chat_id=update.effective_chat.id)
    else:
        await query.edit_message_text(text='Wrong menu button')


def mainloop():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    global logger
    logger = logging.getLogger(__name__)

    BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
    if BOT_TOKEN is not None and BOT_TOKEN != '':
        logger.info('Bot token is set!')
    else:
        logger.error('Bot token env var is not set (TELE_BOT_TOKEN)!')
        exit(1)

    db_setup_redis()

    application = telegram.ext.ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(telegram.ext.CommandHandler('tracks', cmd_tracks))
    application.add_handler(telegram.ext.CommandHandler('debug_tracks', cmd_debug_tracks))
    application.add_handler(telegram.ext.CommandHandler('debug_ping', cmd_debug_ping))
    application.add_handler(telegram.ext.CallbackQueryHandler(cmd_button))
    application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.LOCATION & (~telegram.ext.filters.COMMAND), cmd_message))

    application.run_polling()


if __name__ == '__main__':
    mainloop()
