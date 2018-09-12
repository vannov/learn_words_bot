#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Telegram bot for translating and learning foreign words.
Commands: TODO
"""

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
import logging
import os
import ast
import sys
import json

from translate import calls

#TODO: remove
#os.environ['MASHAPE_KEY'] = 'NLAVwjY9PSmshCLAXj7yilMFLKUap1ukWxxjsn4oSVwFg8VYs3'
#os.environ['TELEGRAM_BOT_TOKEN'] = '526021537:AAFJ3jUDn6ZdPvZW7JFJmOv2OZPq5FtYzaY'

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ.get('PORT', '8443'))

# Callback data
CALLBACK_TYPE_RANDOM = "r"
CALLBACK_TYPE_TRANSLATE = "t"
CALLBACK_TYPE_LEARN = "l"

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


def user_authorized(func):
    """ Decorator for methods requiring admin authorization. """
    def func_wrapper(bot, update):
        user_id = update.message.from_user.id
        admins = ast.literal_eval(os.environ['TELEGRAM_ADMINS'])
        if user_id in admins:
            func(bot, update)
        else:
            update.message.reply_text('Sorry, unauthorized')

    return func_wrapper

# BOT HANDLERS:
def translate(bot, update, word):
    """ Translates the user message into destination language """
    params = {
        'text': word,
        # TODO: get from user
        'src': 'en',
        'dest': 'ru'
    }
    text = calls.google_translate(params)

    button_list = [
        InlineKeyboardButton(text="Learn",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_LEARN, word))),
        InlineKeyboardButton(text="Get random",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_RANDOM, None)))
    ]

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def specific_word(bot, update):
    """ Returns description of requested word. """
    _word(bot, update, update.message.text)

def random_word(bot, update):
    """ Returns random word with description """
    _word(bot, update, None)

def _word(bot, update, word):
    word_dict = calls.get_word(word)
    text = word_dict['word'] + ":\n"
    if 'pronunciation' in word_dict and 'all' in word_dict['pronunciation']:
        text += "[" + word_dict['pronunciation']['all'] + "]\n"
    for r in word_dict['results']:
        text += "\t - " + r['definition'] + "\n"

    word_ = word_dict['word']

    button_list = [
        InlineKeyboardButton(text="Translate",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_TRANSLATE, word_))),
        InlineKeyboardButton(text="Learn",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_LEARN, word_))),
        InlineKeyboardButton(text="Get random",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_RANDOM, word_)))
    ]

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))

    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def learn(bot, update, word):
    """ Saves word to user's list of words to learn """
    #TODO: implement
    error(bot, update, 'Sorry, Learn is not supported yet :(')

def callback_eval(bot, update):
    query_data = update.callback_query.data
    callback_dict = json.loads(query_data)
    if isinstance(callback_dict, dict):
        callback_type = callback_dict['type']
        if callback_type == CALLBACK_TYPE_RANDOM:
            random_word(bot, update)
        elif callback_type == CALLBACK_TYPE_TRANSLATE:
            translate(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_LEARN:
            learn(bot, update, callback_dict['word'])
        else:
            error(bot, update, "Unknown callback type: " + str(callback_type))
    else:
        error(bot, update, "Invalid callback format: " + str(query_data))

def error(bot, update, text):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, text)
    bot.sendMessage(chat_id=get_chat_id(update),
                    text="Error: " + str(text))

# HELPERS
def build_menu(buttons,
               n_cols,
               header_buttons=None,
               footer_buttons=None):
    menu = [buttons[i:i + n_cols] for i in range(0, len(buttons), n_cols)]
    if header_buttons:
        menu.insert(0, header_buttons)
    if footer_buttons:
        menu.append(footer_buttons)
    return menu

def get_chat_id(update):
    if update.callback_query:
        return update.callback_query.message.chat_id
    else:
        return update.message.chat_id

def create_callback_dict(type, word):
    return {
        'type': type,
        'word': word
    }

def main():
    """Start the bot."""

    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("/random", random_word))
    dp.add_handler(CallbackQueryHandler(callback_eval))
    # dp.add_handler(CommandHandler("help", help))

    dp.add_handler(MessageHandler(Filters.text, specific_word))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    if len(sys.argv) > 1 and sys.argv[1] == 'local':
        updater.start_polling()
    else:
        updater.start_webhook(listen="0.0.0.0",
                              port=PORT,
                              url_path=TOKEN)
        updater.bot.set_webhook("https://afternoon-waters-98053.herokuapp.com/" + TOKEN)
    updater.idle()


if __name__ == '__main__':
    main()
