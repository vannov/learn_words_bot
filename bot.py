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
from telegram.parsemode import ParseMode
from googletrans.constants import LANGUAGES
import logging
import os
import ast
import sys
import json
import math


from bot_helpers import calls, store, local

LOCAL_ARGUMENT = 'local'

WEBHOOK_URL = 'https://afternoon-waters-98053.herokuapp.com/'

DEFAULT_SOURCE_LANGUAGE = 'auto'
DEFAULT_TARGET_LANGUAGE = 'en'

LANG_BUTTONS_PER_REPLY = 36

# Callback data
CALLBACK_TYPE_RANDOM = "r"
CALLBACK_TYPE_TRANSLATE = "t"
CALLBACK_TYPE_EXPLAIN = "e"
CALLBACK_TYPE_SAVE = "+"
CALLBACK_TYPE_REMOVE = "-"
CALLBACK_TYPE_SOURCE_LANG = "sl"
CALLBACK_TYPE_TARGET_LANG = "tl"
CALLBACK_TYPE_SOURCE_LANG_PAGE = "slp"
CALLBACK_TYPE_TARGET_LANG_PAGE = "tlp"

SOURCE_LANGUAGE = 1
TARGET_LANGUAGE = 2

COMMANDS =  "/random - get random English word\n"\
            "/saved - get a random word from the list of saved words\n"\
            "/all - get all saved words\n"\
            "/source - select source language\n"\
            "/target - select target language\n"\
            "/show_keyboard - show permanent reply keyboard\n"\
            "/hide_keyboard - hide permanent reply keyboard\n"\
            "/help - print welcome message and instructions\n"

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
    user_id = update.effective_user.id

    src = store_helper.get_src_lang(user_id) if not None else DEFAULT_SOURCE_LANGUAGE
    trg = store_helper.get_trg_lang(user_id) if not None else DEFAULT_TARGET_LANGUAGE

    params = {
        'text': word,
        'src': src,
        'dest': trg
    }
    translation = calls.google_translate(params)

    translation_texts = []
    if isinstance(translation.extra_data['possible-translations'], list) and len(translation.extra_data['possible-translations']) > 0:
        possible_translations = translation.extra_data['possible-translations'][0]
        if isinstance(possible_translations, list) and len(possible_translations) >= 2:
            options = possible_translations[2]
            if isinstance(options, list):
                for option in options:
                    if isinstance(option, list) and len(option) > 0:
                        translation_texts.append(option[0])

    if len(translation_texts) == 0:
        translation_texts.append(translation.text)

    text = ''
    for item in translation_texts:
        text += '– ' + str(item) + '\n'

    button_list = get_save_remove_button_list(user_id, word)

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=1))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def specific_word(bot, update):
    """ Returns description of requested word. """
    _explain_word_google(bot, update, update.message.text)

def random_word(bot, update):
    """ Returns random word with description """
    _word(bot, update, '')

def _random_word_explained_with_google(bot, update):
    """ Get a word from Word API and explanation from Google Translate.
    Currently unused. """
    global store_helper
    user_id = update.effective_user.id
    src = store_helper.get_src_lang(user_id)
    if src == 'en' or src == DEFAULT_SOURCE_LANGUAGE:
        # Get random word from Words API
        word_dict = calls.get_word()
        # Get word explanation and examples from Google Translate.
        _explain_word_google(bot, update, word_dict['word'])
    else:
        src_str = LANGUAGES[src] if src in LANGUAGES else src if not None else "not set"
        text = "Sorry, random word feature is supported only for English source language." \
               "Your current source language: <b>" + src_str + "</b>."
        bot.sendMessage(chat_id=get_chat_id(update), text=text, parse_mode=ParseMode.HTML)

def start(bot, update):
    """ Greets the user and sends list of commands """
    global store_helper
    user_id = update.effective_user.id
    first_name = update.effective_user.first_name

    first_time = False
    if store_helper.get_user_obj(user_id) is None:
        # User ID is not in storage, creating a new record
        src = DEFAULT_SOURCE_LANGUAGE
        lang_code = update.effective_user.language_code[:2]
        trg = lang_code if lang_code in LANGUAGES else DEFAULT_TARGET_LANGUAGE
        store_helper.add_user(user_id, src, trg)
        first_time = True

    text = "Hello, " + first_name + "! This is a word-learning bot. Send any English word or press the button to get a random word." \
            "\n\nList of commands:\n" + COMMANDS
    if first_time:
        text += "\n\nBut first please select your target language:"

    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=get_permanent_reply_keyboard_markup())

    if first_time:
        _show_language_selection(bot=bot, update=update, lang_type=TARGET_LANGUAGE, page=0)

def _word(bot, update, word):
    """ Gets a word from Words API. """
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
    button_list.extend(get_save_remove_button_list(user_id, word))
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup)

def _explain_word_google(bot, update, word):
    """ Uses google translate API to get a word explanation and examples. """
    global store_helper
    user_id = update.effective_user.id

    src = store_helper.get_src_lang(user_id) if not None else DEFAULT_SOURCE_LANGUAGE
    params = {
        'text': word,
        'src': src,
        # Using source language as target on purpose, to get explanation in source language:
        'dest': src
    }
    translation = calls.google_translate(params)
    text = '<b>' + translation.text + ':</b>'
    if translation.pronunciation:
        text += '\n[' + translation.pronunciation + ']'
    if isinstance(translation.extra_data['definitions'], list):
        for definition in translation.extra_data['definitions']:
            if len(definition) >= 2:
                part_of_speech = definition[0]
                text += '\n <i>' + part_of_speech + ':</i>'
                for details in definition[1]:
                    if len(details) > 0:
                        explanation = details[0]
                        text += '\n  – ' + explanation
                        if len(details) >= 3:
                            example = details[2]
                            text += ' <i>"' + example + '"</i>'

    button_list = [
        InlineKeyboardButton(text="Translate",
                             callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_TRANSLATE, word))),
    ]
    user_id = update.effective_user.id
    button_list.extend(get_save_remove_button_list(user_id, word))
    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=2))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)

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

def source(bot, update, page=0):
    """ Starts source language selection dialog. """
    _show_language_selection(bot=bot, update=update, lang_type=SOURCE_LANGUAGE, page=page)

def target(bot, update, page=0):
    """ Starts target language selection dialog. """
    _show_language_selection(bot=bot, update=update, lang_type=TARGET_LANGUAGE, page=page)

def _show_language_selection(bot, update, lang_type, page=0):
    if lang_type == SOURCE_LANGUAGE:
        lang_str = 'source'
        callback_select_type = CALLBACK_TYPE_SOURCE_LANG
        callback_page_type = CALLBACK_TYPE_SOURCE_LANG_PAGE
    elif lang_type == TARGET_LANGUAGE:
        lang_str = 'target'
        callback_select_type = CALLBACK_TYPE_TARGET_LANG
        callback_page_type = CALLBACK_TYPE_TARGET_LANG_PAGE
    else:
        error(bot, update, "Unknown language type: " + str(type))
        return

    global store_helper
    user_id = update.effective_user.id
    src = store_helper.get_src_lang(user_id)
    trg = store_helper.get_trg_lang(user_id)
    src_str = LANGUAGES[src] if src in LANGUAGES else src if not None else "not set"
    trg_str = LANGUAGES[trg] if trg in LANGUAGES else trg if not None else "not set"

    text = "Your current source language: <b>" + str(src_str) + "</b>, target language: <b>" + str(trg_str) + \
           "</b>.\nPlease chose new <b>" + lang_str + "</b> language: "

    button_list = list(map(lambda x: InlineKeyboardButton(text=x[1],
                        callback_data=json.dumps(create_callback_word_dict(callback_select_type, x[0]))),
                    list(LANGUAGES.items())[page * LANG_BUTTONS_PER_REPLY : (page + 1) * LANG_BUTTONS_PER_REPLY]))

    pages_number = math.ceil(len(LANGUAGES) / LANG_BUTTONS_PER_REPLY)
    if pages_number > 1:
        if page > 0:
            button_list.append(InlineKeyboardButton(text="Previous page",
                               callback_data=json.dumps(create_callback_word_dict(callback_page_type, page-1))))
        if page < pages_number - 1:
            button_list.append(InlineKeyboardButton(text="Next page",
                               callback_data=json.dumps(create_callback_word_dict(callback_page_type, page+1))))

    reply_markup = InlineKeyboardMarkup(build_menu(button_list, n_cols=4))
    bot.sendMessage(chat_id=get_chat_id(update), text=text, reply_markup=reply_markup, parse_mode=ParseMode.HTML)


def _set_source_lang(bot, update, lang):
    global store_helper
    user_id = update.effective_user.id
    res = store_helper.set_src_lang(user_id, lang)
    if res == store.Error.SUCCESS or res == store.Error.ALREADY_SAVED:
        lang_str = LANGUAGES[lang]
        bot.sendMessage(chat_id=get_chat_id(update),
                    text="Source language is set to: " + str(lang_str))
    else:
        error(bot, update, "Error changing source language: " + str(res))

def _set_target_lang(bot, update, lang):
    global store_helper
    user_id = update.effective_user.id
    res = store_helper.set_trg_lang(user_id, lang)
    if res == store.Error.SUCCESS or res == store.Error.ALREADY_SAVED:
        lang_str = LANGUAGES[lang]
        bot.sendMessage(chat_id=get_chat_id(update),
                    text="Target language is set to: " + str(lang_str))
    else:
        error(bot, update, "Error changing target language: " + str(res))

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
            _explain_word_google(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_SAVE:
            save(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_REMOVE:
            remove(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_SOURCE_LANG:
            _set_source_lang(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_TARGET_LANG:
            _set_target_lang(bot, update, callback_dict['word'])
        elif callback_type == CALLBACK_TYPE_SOURCE_LANG_PAGE:
            page_number = callback_dict['word']
            source(bot, update, page_number)
        elif callback_type == CALLBACK_TYPE_TARGET_LANG_PAGE:
            page_number = callback_dict['word']
            target(bot, update, page_number)
            pass
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

def get_save_remove_button_list(user_id, word):
    global store_helper
    button_list = []
    already_saved = store_helper.is_saved(user_id, word)
    if already_saved:
        remove_button = InlineKeyboardButton(text="Remove",
                                             callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_REMOVE, word)))
        button_list.append(remove_button)
    else:
        save_button = InlineKeyboardButton(text="Save",
                                           callback_data=json.dumps(create_callback_word_dict(CALLBACK_TYPE_SAVE, word)))
        button_list.append(save_button)
    return button_list

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
    dp.add_handler(CommandHandler("source", source))
    dp.add_handler(CommandHandler("target", target))
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
