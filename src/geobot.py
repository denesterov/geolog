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
            logger.info(f'Static location received. Ignoring. chat_id={update.message.chat.id}, msg_id={update.message.message_id}, usr_id={update.message.from_user.id}')
        else:
            msg = update.message
            new_location = True

    if msg is not None:
        logger.info(f'Location: new={new_location}, chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}, chat_type={msg.chat.type}, loc={msg.location}')
        dt = msg.edit_date if msg.edit_date is not None else msg.date
        common_ts = dt.timestamp() if dt else time.time()
        sess_data = db.get_or_create_session(msg.from_user.id, msg.message_id, msg.chat, msg.location, common_ts)
        if new_location or update_session(sess_data, msg.location, common_ts):
            db.store_location(sess_data, msg.from_user.id, msg.location, common_ts)

        usr_name = update.effective_user.first_name if update.effective_user else 'User'
        if (new_location):
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usr_name} started location recording.')
        elif msg.location.live_period is None:
            db.add_map_job(sess_data['id'])
            await context.bot.send_message(chat_id=update.effective_chat.id, text=f'{usr_name} stopped location recording.')


def update_session(sess_data, loc, common_ts):
    sess_id = sess_data['id']
    last_lat = float(sess_data['last_lat'])
    last_long = float(sess_data['last_long'])
    time_period = common_ts - float(sess_data['last_update'])
    delta = distance.distance((last_lat, last_long), (loc.latitude, loc.longitude)).m
    velocity = delta / time_period if time_period > 0.1 else 100.0 # todo: Do not record overspeed sections

    def finish_segment(sess_data):
        if int(sess_data['track_segm_len']) == 0:
            return None
        segm_id = int(sess_data['track_segm_idx'])
        logger.info(f'update_session. finishing segment. sess_id={sess_id}, segm_id={segm_id}')
        return {
            'track_segm_idx' : segm_id + 1,
            'track_segm_len' : 0,
            'last_update' : common_ts,
        }

    fields = None
    result = None
    if delta < const.MIN_GEO_DELTA:
        logger.info(f'update_session. skip coord update by idle. sess_id={sess_id}, delta={delta:.1f}, dt={time_period:.1f}') # todo: log debug
        if time_period > const.AFTER_PAUSE_TIME:
            fields = finish_segment(sess_data)
            pass
        result = False
    elif velocity > const.MAX_SPEED:
        logger.info(f'update_session. skip coord update by overspeed. sess_id={sess_id}, delta={delta:.1f}, vel={velocity:.1f}') # todo: log debug
        fields = finish_segment(sess_data)
        result = False
    else:
        logger.info(f'update_session. writing update. sess_id={sess_id}, delta={delta:.1f}, vel={velocity:.1f}') # todo: log debug
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
        fields['last_update'] = common_ts
        db.update_session(sess_id, fields)
    return result


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
            wp.lon = pnt.lon
            wp.time = datetime.datetime.fromtimestamp(pnt.timestamp)
            segment.append(wp)
    
    return gpx_inst.to_string()


async def sessions_menu_item(sess_id: str, update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    logger.info(f'sessions_menu_item. sess_id={sess_id}')

    info, segments = db.get_track(sess_id)

    gpx_data = create_gpx_data(segments)

    sess_len = info.length / 1000.0
    sess_dur = info.duration

    ts_str = time.asctime(time.gmtime(info.timestamp))
    descr = f'Here is your track\nStart time {ts_str} UTC\nLength {sess_len:.1f} km, duration {duration_to_human(sess_dur)}, {info.points_total} points'
    
    get_map_res = maps.get_map(sess_id)
    if get_map_res is not None:
        map_file_data, map_filename = get_map_res
        map_file = telegram.InputFile(map_file_data, map_filename)
        await context.bot.send_photo(update.effective_chat.id, map_file, caption=descr)

    sess_tm = datetime.datetime.fromtimestamp(info.timestamp)
    file_name = f'TelegramTrack_{sess_tm.year}{sess_tm.month:02}{sess_tm.day:02}_{sess_tm.hour:02}{sess_tm.minute:02}.gpx'
    gpx_file = telegram.InputFile(gpx_data, file_name)
    await context.bot.send_document(update.effective_chat.id, gpx_file)

    return descr if get_map_res is None else None


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
        descr = await sessions_menu_item(data[1], update, context)
        if descr is None:
            await context.bot.deleteMessage(message_id = update.effective_message.id, chat_id=update.effective_chat.id)
        else:
            await query.edit_message_text(text=descr)
    elif data[0] == 'session_menu':
        usr_id = update.effective_user.id
        logger.info(f'cmd_button. session_menu. usr_id={usr_id}')
        menu_text, menu = sessions_menu_create(usr_id, int(data[1]), int(data[2]))
        await query.edit_message_text(text=menu_text, reply_markup=menu)
    elif data[0] == 'session_cancel':
        await context.bot.deleteMessage(message_id = update.effective_message.id, chat_id=update.effective_chat.id)
    else:
        await query.edit_message_text(text='Wrong menu button')


async def maps_generation_job(context: telegram.ext.CallbackContext):
    await maps.try_create_map()


def mainloop():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )

    BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
    if BOT_TOKEN is not None and BOT_TOKEN != '':
        logger.info('Bot token is set!')
    else:
        logger.error('Bot token env var is not set (TELE_BOT_TOKEN)!')
        exit(1)

    db.setup_redis()

    application = telegram.ext.ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(telegram.ext.CommandHandler('tracks', cmd_tracks))
    application.add_handler(telegram.ext.CommandHandler('debug_tracks', cmd_debug_tracks))
    application.add_handler(telegram.ext.CommandHandler('debug_ping', cmd_debug_ping))
    application.add_handler(telegram.ext.CallbackQueryHandler(cmd_button))
    application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.LOCATION & (~telegram.ext.filters.COMMAND), cmd_message))

    application.job_queue.run_repeating(maps_generation_job, 10.0)

    application.run_polling()


if __name__ == '__main__':
    mainloop()
