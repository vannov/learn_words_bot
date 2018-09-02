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

from translate import calls


TOKEN = os.environ['TELEGRAM_BOT_TOKEN']
PORT = int(os.environ.get('PORT', '8443'))


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
    p = dict()
    p['text'] = update.message.text
    # TODO: get from user
    p['src'] = "en"
    p['dest'] = "ru"
    update.message.reply_text(calls.google_translate(p))

def word(bot, update):
    """ Returns random word with description """
    word_dict = calls.get_word()
    text = word_dict['word'] + ":\n"
    if 'pronunciation' in word_dict and 'all' in word_dict['pronunciation']:
        text += "[" + word_dict['pronunciation']['all'] + "]\n"
    for r in word_dict['results']:
        text += "\t" + r['definition'] + "\n"

    button_list = [
        InlineKeyboardButton(text="Get another", callback_data="another"),
        InlineKeyboardButton(text="Learn", callback_data="learn")
    ]

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))

    bot.sendMessage(chat_id=update.callback_query.message.chat_id, text=text,
                    reply_markup=reply_markup, message_id=update.callback_query.message.message_id)

def callback_eval(bot, update):
    query_data = update.callback_query.data
    update.message.reply_text(query_data)

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
    dp.add_handler(CommandHandler("word", word))
    dp.add_handler(CallbackQueryHandler(callback_eval))
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
