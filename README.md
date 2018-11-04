## Telegram bot for translating and learning foreign words

Example of a working bot: https://t.me/lwords_bot
Please note that currently the bot is hosted on a free Heroku server, which goes to sleep after 30 minutes of inactivity. So it can take up to 10 seconds for the bot to wake up and reply.  

###How to use the bot:

Start chatting with bot and it will send you the instructions and list of commands. You can always get these instructions again by sending **/help** command.

#####Typical commands:

Use commands **/source** and **/target** to choose your source (foreign) and target (native) languages:
 
![Selecting language](https://i.imgur.com/DppoUEbl.jpg)
 
Send any word in chosen foreign language to get it's explanation. Use inline buttons to translate it to your native language or to save from the list of words you want to learn:

![Sending a word](https://i.imgur.com/7JD4HlXl.jpg)

Use **/saved** command to get a word from the list of your saved words in order to practice. Once you learned the word, you can use the inline button to remove this word from your list:

![Getting a saved word](https://i.imgur.com/bp6kOjTl.jpg)

Use **/random** command to get random English word of phrase:

![Getting a random word](https://i.imgur.com/TdP1o18l.jpg)

###Implementation details:

The bot is implemented in Python. The start point is function main() in [bot.py](bot.py).

Major dependencies:

- Telegram bot routines are implemented using python-telegram-bot library: https://github.com/python-telegram-bot/python-telegram-bot
- "Translate" and "Explain" functionality is powered by Google Translate API through Googletrans python library: https://github.com/ssut/py-googletrans/  
- Random word functionality is powered by Words API: https://www.wordsapi.com/
- [Redis](https://redis.io/) is used as a database, implemented using Redis Python client: https://github.com/andymccurdy/redis-py

Third party Python packages are managed using Pipenv: https://pipenv.readthedocs.io/en/latest/
See [Pipfile](Pipfile) for all Python dependencies.


###Developer notes:

#####Running on server:
By default the bot runs using [webhooks](https://core.telegram.org/bots/api#setwebhook), which requires a server with a domain name.

Before starting the bot script, set up the following environment variables on your server:
- TELEGRAM_BOT_TOKEN: Telegram bot token. Use [BotFather](https://telegram.me/botfather) to create a new Telegram Bot.
- WEBHOOK_URL: Bot webhook server URL (your server domain name).
- REDIS_URL: Redis storage URL.
- MASHAPE_KEY: Words API token (see https://www.wordsapi.com/).

Run this command to start the bot on your server:
```
python bot.py
```

#####Running on local machine:
You can run the bot on a local machine using [polling](https://core.telegram.org/bots/api#getupdates).

Before starting the bot script, modify [local.py](helpers/local.py) file to set up necessary environment variables. 

Run this command to start the bot on your local machine:
```
python bot.py local
```