## Geo logging Telegram Bot

## How to use
### Start the bot
* put you bot token into `bot_token.txt` file next to python sources
* `make setup`
* `make run`
### Telegram
* share you location with bot in private or group chat
* use bot's menu to download you tracks as GPX

## Starting Redis Stack
```
docker run -d --name redis-stack -p 6379:6379 -p 8001:8001 redis/redis-stack:latest
```
or just `docker start redis-stack` later
