import os
import logging
import redis
import asyncio
import telegram

# from telegram import Update
# from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

if __name__ != '__main__':
    exit(1)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


BOT_TOKEN = os.environ.get('TELE_BOT_TOKEN')
if BOT_TOKEN is None:
    print('Bot tag env var is not set (TELE_BOT_TOKEN)!')
    exit(1)
else:
    print('Bot token is set!')


async def test_bot():
    bot = telegram.Bot(BOT_TOKEN)
    async with bot:
        res = await bot.get_me()
        print('Bot test result:')
        print(res)
asyncio.run(test_bot())


# async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
#     await update.message.reply_text(f'Hello {update.effective_user.first_name}')


# app = ApplicationBuilder().token("YOUR TOKEN HERE").build()

# app.add_handler(CommandHandler("hello", hello))

# app.run_polling()
