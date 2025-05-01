import os
import logging
import redis
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import uuid
import time
import telegram
import telegram.ext


# import redis.commands.search.aggregation as aggregations
# import redis.commands.search.reducers as reducers
# from redis.commands.json.path import Path
# 


logger = None
redis_db = None

def db_get_redis():
    global redis_db
    if redis_db is None:
        redis_db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
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


def db_get_session(usr_id, msg_id, tg_chat):
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
            'ts' : time.time(),
        }
        new_res = r.hset(uid, mapping=session)
        logger.info(f'New session. usr_id={usr_id}, uid={uid}, res={new_res}')
        return uid
    else:
        assert res.total == 1
        doc = res.docs[0]
        logger.info(f'Found old session for usr_id={usr_id}, sess={doc}')
        return doc.id


def db_store_location(sess_id, usr_id, loc):
    r = db_get_redis()
    uid = f'point:{uuid.uuid1()}'
    point = {
        'sess_id' : sess_id,
        'usr_id' : usr_id,
        'latitude' : loc.latitude,
        'longitude' : loc.longitude,
        'ts' : time.time(),
    }
    r.hset(uid, mapping=point)
    logger.info(f'Location stored. sess_id={sess_id}, usr_id={usr_id}')


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
        sess_id = db_get_session(msg.from_user.id, msg.message_id, msg.chat)
        db_store_location(sess_id, msg.from_user.id, msg.location)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your location updated. new={new_location}')


async def cmd_trace(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    usr_id = update.effective_user.id
    logger.info(f'Trace Chat Command. usr_id={usr_id}')
    r = db_get_redis()
    sess_idx = r.ft('idx:session')
    point_idx = r.ft('idx:point')
    res = sess_idx.search(Query(f'@usr_id:[{usr_id} {usr_id}]'))
    logger.info(f'Trace Chat Command. sessions_found={res.total}')

    lines = [f'Hello {update.effective_user.first_name} here is your traces:\n\n']
    for doc in res.docs:
        sess_id = doc.id
        sess_id_tr = sess_id.replace(':', '\\:').replace('-', '\\-')
        q = f'@sess_id:{{{sess_id_tr}}}'
        logger.info(f'Trace Chat Command. query={q}')
        pnt_res = point_idx.search(Query(q).dialect(2))
        ts = float(doc.ts)
        tm = time.asctime(time.gmtime(ts))
        lines.append(f'Trace: {doc.chat_name}, {tm}, {pnt_res.total} points\nid {sess_id}\n\n')
    
    await context.bot.send_message(chat_id=update.effective_chat.id, text=''.join(lines))


def fibo(n: int):
    if n <= 1:
        return n
    return fibo(n - 1) + fibo(n - 2)


def create_menu(start: int, span: int):
    logger.info(f'Creating menu: {start} - {span}')
    keyboard = []
    for i in range(start, start + span):
        keyboard.append([telegram.InlineKeyboardButton(f'Option {fibo(i)}', callback_data=f'get {i}')])

    keyboard.append([
        telegram.InlineKeyboardButton('Prev', callback_data=f'menu {start - span} {span}'),
        telegram.InlineKeyboardButton('Next', callback_data=f'menu {start + span} {span}'),
    ])

    return telegram.InlineKeyboardMarkup(keyboard)

async def cmd_test_menu(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    #  keyboard = [
    #    [
    #         telegram.InlineKeyboardButton("Option 1", callback_data="1"),
    #         telegram.InlineKeyboardButton("Option 2", callback_data="2"),
    #     ],
    #     [telegram.InlineKeyboardButton("Option 3", callback_data="3")],
    # ]
    # reply_markup = telegram.InlineKeyboardMarkup(keyboard)

    await update.message.reply_text('Your menu', reply_markup=create_menu(0, 10))


async def cmd_test_button(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query

    # CallbackQueries need to be answered, even if no notification to the user is needed
    # Some clients may have trouble otherwise. See https://core.telegram.org/bots/api#callbackquery
    await query.answer()

    data = query.data.split(' ')
    if data[0] == 'get':
        num = int(data[1])
        await query.edit_message_text(text=f'You selected number {num}')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your number is {fibo(num)}')
    elif data[0] == 'menu':
        fromm = int(data[1])
        to = int(data[2])
        await query.edit_message_text(text='Your menu', reply_markup=create_menu(fromm, to))
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
    if BOT_TOKEN is None:
        logger.error('Bot token env var is not set (TELE_BOT_TOKEN)!')
        exit(1)
    else:
        logger.info('Bot token is set!')

    db_setup_redis()

    application = telegram.ext.ApplicationBuilder().token(BOT_TOKEN).build()

    application.add_handler(telegram.ext.CommandHandler('trace', cmd_trace))
    application.add_handler(telegram.ext.CommandHandler('test_menu', cmd_test_menu))
    application.add_handler(telegram.ext.CallbackQueryHandler(cmd_test_button))
    application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.LOCATION & (~telegram.ext.filters.COMMAND), cmd_message))

    application.run_polling()


if __name__ == '__main__':
    mainloop()
