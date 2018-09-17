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
from translate import store

#TODO: remove
# os.environ['MASHAPE_KEY'] = 'NLAVwjY9PSmshCLAXj7yilMFLKUap1ukWxxjsn4oSVwFg8VYs3'
# os.environ['TELEGRAM_BOT_TOKEN'] = '526021537:AAFJ3jUDn6ZdPvZW7JFJmOv2OZPq5FtYzaY'
# os.environ['REDIS_URL'] = 'redis://h:p2a1b69e6106ff91736dd446c786cecfd24a56ca4589c2ae34867b32371ea8ef3@ec2-52-204-102-201.compute-1.amazonaws.com:63269'

TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ.get('PORT', '8443'))

# Callback data
CALLBACK_TYPE_RANDOM = "r"
CALLBACK_TYPE_TRANSLATE = "t"
CALLBACK_TYPE_EXPLAIN = "e"
CALLBACK_TYPE_SAVE = "+"
CALLBACK_TYPE_REMOVE = "-"


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

# Global store instance
store_helper = None


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
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_SAVE, word))),
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

def start(bot, update):
    """ Greets the user and sends list of commands """
    text = "Hello! This is a word-learning bot. Send any english word or press the button to get a random word"
    button_list = [
        InlineKeyboardButton(text="Get random",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_RANDOM, None)))
    ]

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

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
        InlineKeyboardButton(text="Save",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_SAVE, word_))),
        InlineKeyboardButton(text="Get random",
                             callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_RANDOM, word_)))
    ]

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))

    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def save(bot, update, word):
    """ Saves word to user's list of words to learn """
    global store_helper
    user_id = update.effective_user.id
    res = store_helper.add_word(user_id, word)
    if res == store.Error.SUCCESS:
        bot.sendMessage(chat_id=get_chat_id(update),
                    text="Saved to the list of words to learn.")
    else:
        error(bot, update, "Error saving: " + str(res))

def remove(bot, update, word):
    """ Remove word from user's list of words to learn """
    global store_helper
    user_id = update.effective_user.id
    res = store_helper.remove_word(user_id, word)
    if res == store.Error.SUCCESS:
        bot.sendMessage(chat_id=get_chat_id(update),
                        text="Removed from the list of words to learn.")
    else:
        error(bot, update, "Error removing: " + str(res))

def get_saved(bot, update):
    """ Gets a word from the user's list of words to learn. """
    global store_helper
    user_id = update.effective_user.id
    word = store_helper.get_word(user_id)
    if word is not None:
        button_list = [
            InlineKeyboardButton(text="Explain",
                                 callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_EXPLAIN, word))),
            InlineKeyboardButton(text="Translate",
                                 callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_TRANSLATE, word))),
            InlineKeyboardButton(text="Remove",
                                 callback_data=json.dumps(create_callback_dict(CALLBACK_TYPE_REMOVE, word)))
        ]

        reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=3))

        bot.sendMessage(chat_id=get_chat_id(update), text=word, reply_markup=reply_markup)
    else:
        error(bot, update, "No saved words found.")

def get_all_saved(bot, update):
    """ Gets all word from the user's list of words to learn. """
    global store_helper
    user_id = update.effective_user.id
    words = store_helper.get_all_words(user_id)
    if isinstance(words, list):
        bot.sendMessage(chat_id=get_chat_id(update), text=str(words))
    else:
        error(bot, update, "No saved words found.")

def callback_eval(bot, update):
    query_data = update.callback_query.data
    callback_dict = json.loads(query_data)
    if isinstance(callback_dict, dict):
        callback_type = callback_dict['type']
        if callback_type == CALLBACK_TYPE_RANDOM:
            random_word(bot, update)
        elif callback_type == CALLBACK_TYPE_TRANSLATE:
            translate(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_EXPLAIN:
            _word(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_SAVE:
            save(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_REMOVE:
            remove(bot, update, callback_dict['word'])
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
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("random", random_word))
    dp.add_handler(CommandHandler("saved", get_saved))
    dp.add_handler(CommandHandler("all", get_all_saved))
    dp.add_handler(CallbackQueryHandler(callback_eval))
    dp.add_handler(CommandHandler("help", start))

    dp.add_handler(MessageHandler(Filters.text, specific_word))

    # log all errors
    dp.add_error_handler(error)

    # Initialize Store
    global store_helper
    store_helper = store.Store()

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
