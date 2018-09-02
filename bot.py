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

from translate import calls


TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ.get('PORT', '8443'))

# Callback data
CALLBACK_DATA_ANOTHER = "another"
CALLBACK_DATA_TRANSLATE = "translate"
CALLBACK_DATA_LEARN = "learn"

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
def translate(bot, update):
    """ Translates the user message into destination language """
    message = update.callback_query.message if update.callback_query else update.message
    p = dict()
    p['text'] = message.text
    # TODO: get from user
    p['src'] = "en"
    p['dest'] = "ru"

    message.reply_text(calls.google_translate(p))

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
        text += "\t" + r['definition'] + "\n"

    button_list = [
        InlineKeyboardButton(text="Get another", callback_data=CALLBACK_DATA_ANOTHER),
        InlineKeyboardButton(text="Translate", callback_data=CALLBACK_DATA_TRANSLATE)
    ]

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

    chat_id = update.callback_query.message.chat_id if update.callback_query else update.message.chat_id
    bot.sendMessage(chat_id=chat_id, text=text, reply_markup=reply_markup)

def callback_eval(bot, update):
    query_data = update.callback_query.data
    if query_data == CALLBACK_DATA_ANOTHER:
        random_word(bot, update)
    elif query_data == CALLBACK_DATA_TRANSLATE:
        translate(bot, update)
    else:
        bot.sendMessage(chat_id=update.callback_query.message.chat_id,
                        text="Unknown callback: " + str(query_data))

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

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

def main():
    """Start the bot."""

    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("word", random_word))
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
