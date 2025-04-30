import os
import logging
import redis
from redis.commands.search.field import TextField, NumericField, TagField
from redis.commands.search.indexDefinition import IndexDefinition, IndexType
from redis.commands.search.query import Query
import uuid
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
#   ts = 441818433,
#   loc = {
#     lat = 33.3,
#     long = 55.5,
#   }
# }
#
# session = {
#   usr_id = 100500,
#   chat_id = 100600,
#   msg_id = 100800,
#   chat_type = "PUB|PRIV"
#   chat_name = "EUC Tusovka"
# }


def db_setup_redis():
    r = db_get_redis()

    sess_index = r.ft('idx:session')
    if sess_index is None:
        logger.info('Creating index for sessions')
        sess_schema = (
            NumericField('usr_id'),
            NumericField('chat_id'),
            NumericField('msg_id'),
            TagField('chat_type'),
        )
        sess_index.create_index(
            sess_schema,
            definition=IndexDefinition(prefix=['session:'], index_type=IndexType.HASH),
        )

    point_index = r.ft('idx:point')
    if point_index is None:
        logger.info('Creating index for points')
        point_schema = (
            TextField('sess_id'),
            NumericField('ts'),
        )
        point_index.create_index(
            point_schema,
            definition=IndexDefinition(prefix=['point:'], index_type=IndexType.HASH),
        )

    logger.info('Redis is ready')


def db_get_session(usr_id, chat_id, msg_id, chat_type):
    r = db_get_redis()
    chat_tp = 'PRIV' if chat_type == 'PRIVATE' else 'PUB'
    idx = r.ft('idx:session')
    res = idx.search(Query(f'{usr_id}'))
    logger.info(f'Session search:{res}')
    if res.total == 0:
        logger.info(f'Creating new session for usr_id={usr_id}')
        uid = uuid.uuid1()
        session = {
            'usr_id' : usr_id,
            'chat_id' : chat_id,
            'msg_id' : msg_id,
            'chat_type' : chat_tp,
        }
        new_res = r.hset(f'session:{uid}', mapping=session)
        logger.info(f'New session. usr_id={usr_id}, res={new_res}')
    else:
        assert res.total == 1
        doc = res.docs[0]
        logger.info(f'Found old session for usr_id={usr_id}, sess={doc}')


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
        logger.info(f'Location: new={new_location}, chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}, loc={msg.location}')
        db_get_session(msg.from_user.id, msg.chat.id, msg.message_id, msg.chat.type)
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Your location updated. new={new_location}')


async def cmd_trace(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f'Hello {update.effective_user.first_name} here is your trace...')


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
    application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.LOCATION & (~telegram.ext.filters.COMMAND), cmd_message))

    application.run_polling()


if __name__ == '__main__':
    mainloop()
