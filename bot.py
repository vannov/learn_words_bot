#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Telegram bot for translating and learning foreign words.
Commands: TODO
"""

from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters
from telegram.inline.inlinekeyboardbutton import InlineKeyboardButton
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.keyboardbutton import KeyboardButton
from telegram.replykeyboardmarkup import ReplyKeyboardMarkup
from telegram.replykeyboardremove import ReplyKeyboardRemove
import logging
import os
import ast
import sys
import json


from translate import calls, store, local

LOCAL_ARGUMENT = 'local'

WEBHOOK_URL = 'https://afternoon-waters-98053.herokuapp.com/'

# TODO: get from user
SOURCE_LANGUAGE = 'en'
TARGET_LANGUAGE = 'ru'

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
    global store_helper
    params = {
        'text': word,
        'src': SOURCE_LANGUAGE,
        'dest': TARGET_LANGUAGE
    }
    text = calls.google_translate(params)

    button_list = []

    user_id = update.effective_user.id
    already_saved = store_helper.is_saved(user_id, word)
    if already_saved:
        remove_button = InlineKeyboardButton(text="Remove",
                                             callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_REMOVE, word)))
        button_list.append(remove_button)
    else:
        save_button = InlineKeyboardButton(text="Save",
                                           callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_SAVE, word)))
        button_list.append(save_button)

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
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
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=get_permanent_reply_keyboard_markup())

def _word(bot, update, word):
    global store_helper
    word_dict = calls.get_word(word)
    text = word_dict['word'] + ":\n"
    if 'pronunciation' in word_dict and 'all' in word_dict['pronunciation']:
        text += "[" + word_dict['pronunciation']['all'] + "]\n"
    for r in word_dict['results']:
        text += "\t - " + r['definition'] + "\n"

    word_ = word_dict['word']

    button_list = [
        InlineKeyboardButton(text="Translate",
                             callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_TRANSLATE, word_))),
    ]

    user_id = update.effective_user.id
    already_saved = store_helper.is_saved(user_id, word_)
    if already_saved:
        remove_button = InlineKeyboardButton(text="Remove",
                                             callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_REMOVE, word)))
        button_list.append(remove_button)
    else:
        save_button = InlineKeyboardButton(text="Save",
                                           callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_SAVE, word)))
        button_list.append(save_button)

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

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
                                 callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_EXPLAIN, word))),
            InlineKeyboardButton(text="Translate",
                                 callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_TRANSLATE, word))),
            InlineKeyboardButton(text="Remove",
                                 callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_REMOVE, word)))
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

def show_keyboard(bot, update):
    """ Shows permanent reply keyboard """
    text = "Reply keyboard shown"
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=get_permanent_reply_keyboard_markup())

def hide_keyboard(bot, update):
    """ Hides permanent reply keyboard """
    text = "Reply keyboard hidden"
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=ReplyKeyboardRemove())

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

def create_callback_word_dict(type, word):
    return {
        'type': type,
        'word': word
    }

def get_permanent_reply_keyboard_markup():
    button_list = [
        [ KeyboardButton(text="/random"), KeyboardButton(text="/saved") ],
        [ KeyboardButton(text="/all"), KeyboardButton(text="/help")]
    ]
    return ReplyKeyboardMarkup(keyboard=button_list)

def main():
    """Start the bot."""

    local_run = False
    if len(sys.argv) > 1 and sys.argv[1] == LOCAL_ARGUMENT:
        local_run = True

    if local_run:
        # Setting environment variables when running on a local machine
        local.set_env_viariables()

    token = os.environ['TELEGRAM_BOT_TOKEN']
    port = int(os.environ.get('PORT', '8443'))

    updater = Updater(token)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("random", random_word))
    dp.add_handler(CommandHandler("saved", get_saved))
    dp.add_handler(CommandHandler("all", get_all_saved))
    dp.add_handler(CommandHandler("show_keyboard", show_keyboard))
    dp.add_handler(CommandHandler("hide_keyboard", hide_keyboard))
    dp.add_handler(CommandHandler("help", start))
    dp.add_handler(CallbackQueryHandler(callback_eval))

    dp.add_handler(MessageHandler(Filters.text, specific_word))

    # log all errors
    dp.add_error_handler(error)

    # Initialize Store
    global store_helper
    store_helper = store.Store()

    # Start the Bot. Use polling when running on a local machine, otherwise use webhooks.
    if local_run:
        updater.start_polling()
    else:
        updater.start_webhook(listen="0.0.0.0",
                              port=port,
                              url_path=token)
        updater.bot.set_webhook(WEBHOOK_URL + token)
    updater.idle()


if __name__ == '__main__':
    main()
