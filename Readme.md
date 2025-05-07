## Geo logging Telegram Bot

## How to use

### Native start

Start Redis Stack container:
```
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```
or just `docker start redis-stack` later

Start the bot:
* `make setup`
* put your bot token into `bot_token.txt` file next to python sources (handy for developer usage)
* `make run`
OR
* `TELE_BOT_TOKEN=<Your_Telegram_Token> make run_env_token`

### Docker start
Go to `deploy` folder and then:
```
TELE_BOT_TOKEN=<Your_Telegram_Token> docker-compose up --build -d
```

### Telegram
* Share you location with bot in a private or group chat
* Use bot's menu to download you tracks as GPX
