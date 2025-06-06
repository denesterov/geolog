import os
import math
import logging
import time
import datetime
import telegram
import telegram.ext
from geopy import distance
import const
import gpx
import base64
import uuid

import db
import maps

logger = logging.getLogger('geobot-main')


async def cmd_message(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    msg = None
    new_location = None

    if update.edited_message is not None and update.edited_message.location is not None:
        msg = update.edited_message
        new_location = False
    elif update.message is not None and update.message.location is not None:
        if update.message.location.live_period is None:
            logger.info(f'cmd_message. Static location received. Ignoring. chat_id={update.message.chat.id}, msg_id={update.message.message_id}, usr_id={update.message.from_user.id}')
        else:
            msg = update.message
            new_location = True

    if msg is not None:
        logger.info(f'cmd_message. Location. new={new_location}, chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}, chat_type={msg.chat.type}, loc={msg.location}')
        dt = msg.edit_date if msg.edit_date is not None else msg.date
        common_ts = dt.timestamp() if dt else time.time()
        sess_data = db.get_or_create_session(msg.from_user.id, msg.message_id, msg.chat, msg.location, common_ts)
        if new_location or update_session(sess_data, msg.location, common_ts):
            db.store_location(sess_data, msg.from_user.id, msg.location, common_ts)

        usr_name = update.effective_user.first_name if update.effective_user else 'User'
        if (new_location):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usr_name} started location recording.')
        elif msg.location.live_period is None:
            logger.info(f'cmd_message. Translation stopped. chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}')
            db.add_map_job(sess_data['id'])
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usr_name} stopped location recording.')


def update_session(sess_data, loc, common_ts):
    sess_id = sess_data['id']

    track_segm_len = int(sess_data['track_segm_len'])

    last_lat = float(sess_data['last_lat'])
    last_long = float(sess_data['last_long'])
    time_period = common_ts - float(sess_data['last_update'])
    delta = distance.distance((last_lat, last_long), (loc.latitude, loc.longitude)).m
    velocity = delta / time_period if time_period > 0.1 else 0.0

    fields = {}

    def finish_segment():
        if track_segm_len == 0:
            return
        segm_id = int(sess_data['track_segm_idx'])
        logger.info(f'update_session. finishing segment. sess_id={sess_id}, segm_id={segm_id}, prev_segm_len={track_segm_len}')
        fields['track_segm_idx'] = segm_id + 1
        fields['track_segm_len'] = 0

    do_store_point = None
    if delta < const.MIN_GEO_DELTA:
        logger.info(f'update_session. skip coord update by idle. sess_id={sess_id}, delta={delta:.1f}, dt={time_period:.1f}') # todo: log debug
        if time_period > const.AFTER_PAUSE_TIME:
            finish_segment()
            fields['last_update'] = common_ts
        do_store_point = False
    elif velocity > const.MAX_SPEED:
        logger.info(f'update_session. skip coord update by overspeed. sess_id={sess_id}, delta={delta:.1f}, vel={velocity:.1f}') # todo: log debug
        finish_segment()
        fields['last_lat'] = loc.latitude
        fields['last_long'] = loc.longitude
        fields['last_update'] = common_ts
        do_store_point = False
    else:
        logger.info(f'update_session. writing update. sess_id={sess_id}, delta={delta:.1f}, vel={velocity:.1f}, dt={time_period:.1f}') # todo: log debug
        fields['last_lat'] = loc.latitude
        fields['last_long'] = loc.longitude
        fields['last_update'] = common_ts
        if track_segm_len > 0:
            fields['length'] = float(sess_data['length']) + delta
            fields['duration'] = float(sess_data['duration']) + time_period
        fields['track_segm_len'] = track_segm_len + 1
        do_store_point = True

    if len(fields) > 0:
        db.update_session(sess_id, fields)
    return do_store_point


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


def create_gpx_data(segments):
    gpx_inst = gpx.GPX()
    gpx_inst.name = 'Telegram GPS track'
    gpx_inst.creator='Geograph'
    gpx_inst.descr = 'This GPX file was created by Geograph Telegram Bot'
    gpx_inst.tracks.append(gpx.track.Track())

    for segm_points in segments:
        gpx_inst.tracks[0].segments.append(gpx.track_segment.TrackSegment())
        segment = gpx_inst.tracks[0].segments[-1]
        for pnt in segm_points:
            wp = gpx.Waypoint()
            wp.lat = pnt.lat
            wp.lon = pnt.long
            wp.time = datetime.datetime.fromtimestamp(pnt.ts)
            segment.append(wp)
    
    return gpx_inst.to_string()


async def output_track_to_chat(sess_id: str, update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logger.info(f'output_track_to_chat. sess_id={sess_id}')

    info, segments = db.get_track(sess_id)

    gpx_data = create_gpx_data(segments)

    sess_len = info.length / 1000.0
    sess_dur = info.duration

    ts_str = time.asctime(time.gmtime(info.timestamp))
    descr = f'Here is the track\n' \
        f'Start time {ts_str} UTC\n' \
        f'Length {sess_len:.1f} km, duration {duration_to_human(sess_dur)}\n' \
        f'Link to share this track: {form_deep_link(sess_id)}'
    
    get_map_res = maps.get_map(sess_id)
    if get_map_res is not None:
        map_file_data, map_filename = get_map_res
        map_file = telegram.InputFile(map_file_data, map_filename)
        await context.bot.send_photo(update.effective_chat.id, map_file, caption=descr)
    else:
        await context.bot.send_message(chat_id = update.effective_chat.id, text=descr)

    sess_tm = datetime.datetime.fromtimestamp(info.timestamp)
    file_name = f'TelegramTrack_{sess_tm.year}{sess_tm.month:02}{sess_tm.day:02}_{sess_tm.hour:02}{sess_tm.minute:02}.gpx'
    gpx_file = telegram.InputFile(gpx_data, file_name)
    await context.bot.send_document(update.effective_chat.id, gpx_file)


def parse_deep_link(args):
    logger.info(f'parse_deep_link. args={args}')
    if (len(args) == 1 and type(args[0]) == str):
        b64 = base64.b64decode(args[0])
        if len(b64) == 16:
            try:
                sess_uuid = uuid.UUID(bytes = b64)
                logger.info(f'parse_deep_link. sess_uuid={sess_uuid}')
                return 'session:' + str(sess_uuid)
            except ValueError:
                pass
    return None


def form_deep_link(sess_id: str):
    uid = db.get_uid_from_sess_id(sess_id)
    uid64 = base64.b64encode(uid.bytes)
    return f'https://t.me/{const.GEOLOG_BOT_NAME}?start={uid64.decode("utf-8")}'


async def sessions_menu_item(sess_id: str, update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logger.info(f'sessions_menu_item. sess_id={sess_id}')
    await output_track_to_chat(sess_id, update, context)


def sessions_menu_create(usr_id: int, offset: int, page: int):
    logger.info(f'sessions_menu_create. offset={offset}, page={page}')

    sessions, sess_total = db.get_sessions(usr_id, offset, page, False)

    keyboard = []
    for sess in sessions:
        length = sess.length / 1000.0
        age = time.time() - sess.timestamp
        descr = f'{duration_to_human(age)} ago, {length:.1f} km'
        keyboard.append([telegram.InlineKeyboardButton(descr, callback_data=f'session_menu_item {sess.id}')])

    navig_butts = []
    if offset >= page:
        navig_butts.append(telegram.InlineKeyboardButton('Prev', callback_data=f'session_menu {offset - page} {page}'))
    if len(sessions) >= page:
        navig_butts.append(telegram.InlineKeyboardButton('Next', callback_data=f'session_menu {offset + page} {page}'))
    navig_butts.append(telegram.InlineKeyboardButton('Cancel', callback_data=f'session_cancel'))
    keyboard.append(navig_butts)

    return (f'Records from {offset} to {min(offset + page, sess_total)} of {sess_total}', telegram.InlineKeyboardMarkup(keyboard))


async def cmd_start(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    usr_id = update.effective_user.id
    logger.info(f'cmd_start. usr_id={usr_id}, args={context.args}')
    if context.args is not None and len(context.args) == 1:
        logger.debug(f'cmd_start. deeplink. usr_id={usr_id}')
        await context.bot.deleteMessage(message_id=update.effective_message.id, chat_id=update.effective_chat.id)
        sess_id = parse_deep_link(context.args)
        if sess_id is not None:
            await output_track_to_chat(sess_id, update, context)
        else:
            await update.message.reply_text(f'Wrong deep link.')
    else:
        logger.debug(f'cmd_start. general start. usr_id={usr_id}, msg={update.message}')
        await update.message.reply_text(f'Welcome to GeoGraph bot. Share your location to start recording.')


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
    sessions, sess_total = db.get_sessions(usr_id, 0, 10, True)

    lines = [f'Hello {update.effective_user.first_name} here is your last tracks:\n(You have {sess_total} total tracks)\n\n']
    for sess in sessions:
        tm = time.asctime(time.gmtime(sess.timestamp))
        lines.append(f'Track: {sess.id}\n{tm}\nChat: {sess.chat_name}\nLength {sess.length} m, duration {sess.duration} s, {sess.points_num} points\n\n')
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(lines))


async def cmd_button(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    data = query.data.split(' ')
    if data[0] == 'session_menu_item':
        await context.bot.deleteMessage(message_id=update.effective_message.id, chat_id=update.effective_chat.id)
        await sessions_menu_item(data[1], update, context)
    elif data[0] == 'session_menu':
        usr_id = update.effective_user.id
        logger.info(f'cmd_button. session_menu. usr_id={usr_id}')
        menu_text, menu = sessions_menu_create(usr_id, int(data[1]), int(data[2]))
        await query.edit_message_text(text=menu_text, reply_markup=menu)
    elif data[0] == 'session_cancel':
        await context.bot.deleteMessage(message_id=update.effective_message.id, chat_id=update.effective_chat.id)
    else:
        await query.edit_message_text(text='Wrong menu button')


async def maps_generation_job(context: telegram.ext.CallbackContext):
    await maps.try_create_map()


def mainloop():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    const.setup()

    db.setup_redis()

    application = telegram.ext.ApplicationBuilder().token(const.BOT_TOKEN).build()

    application.add_handler(telegram.ext.CommandHandler('start', cmd_start))
    application.add_handler(telegram.ext.CommandHandler('tracks', cmd_tracks))
    application.add_handler(telegram.ext.CommandHandler('debug_tracks', cmd_debug_tracks))
    application.add_handler(telegram.ext.CommandHandler('debug_ping', cmd_debug_ping))
    application.add_handler(telegram.ext.CallbackQueryHandler(cmd_button))
    application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.LOCATION & (~telegram.ext.filters.COMMAND), cmd_message))

    application.job_queue.run_repeating(maps_generation_job, 10.0)

    application.run_polling()


if __name__ == '__main__':
    mainloop()
