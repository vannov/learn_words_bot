#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Telegram bot for translating and learning foreign words.
Commands: TODO
"""

from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
import logging
import os

from translate import calls


TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ.get('PORT', '8443'))


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# BOT HANDLERS:
def translate(bot, update):
    """ Translates the user message into destination language """
    p = dict()
    p['text'] = update.message.text
    # TODO: get from user
    p['src'] = "en"
    p['dest'] = "ru"
    update.message.reply_text(calls.google_translate(p))

def word(bot, update):
    """ Returns random word with description """
    word_dict = calls.get_word()
    output = word_dict['word'] + ":\n"
    for r in word_dict['results']:
        res = "\t" + r['definition'] + "\n"
    update.message.reply_text(output)

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""

    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("word", word))
    # dp.add_handler(CommandHandler("help", help))

    # on noncommand i.e message - echo the message on Telegram
    dp.add_handler(MessageHandler(Filters.text, translate))

    # log all errors
    dp.add_error_handler(error)

    updater.start_webhook(listen="0.0.0.0",
                          port=PORT,
                          url_path=TOKEN)
    updater.bot.set_webhook("https://afternoon-waters-98053.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()
