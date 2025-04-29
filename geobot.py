import os
import logging
import redis
import telegram
import telegram.ext

# from telegram import Update
# from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes


if __name__ != '__main__':
    exit(1)


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
if BOT_TOKEN is None:
    print('Bot tag env var is not set (TELE_BOT_TOKEN)!')
    exit(1)
else:
    print('Bot token is set!')


async def cmd_message(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    if update.edited_message is not None:
        msg = update.edited_message
        logger.info(f'Location UPDATED: chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}, loc={msg.location}')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Your location updated")
    elif update.message is not None:
        msg = update.message
        logger.info(f'NEW Location: chat_id={msg.chat.id}, msg_id={msg.message_id}, usr_id={msg.from_user.id}, loc={msg.location}')
        await context.bot.send_message(chat_id=update.effective_chat.id, text=f"New location from you")
    # await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello {update.effective_user.first_name}, your location saved")

async def cmd_trace(update: telegram.Update, context: telegram.ext.ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text=f"Hello {update.effective_user.first_name} here is your trace...")

application = telegram.ext.ApplicationBuilder().token(BOT_TOKEN).build()

application.add_handler(telegram.ext.CommandHandler('trace', cmd_trace))
application.add_handler(telegram.ext.MessageHandler(telegram.ext.filters.LOCATION & (~telegram.ext.filters.COMMAND), cmd_message))

application.run_polling()
