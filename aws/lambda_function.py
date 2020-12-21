import os
import json
import requests
from googletrans import Translator

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
TELEGRAM_REPLY_URL = "https://api.telegram.org/bot{}/".format(TELEGRAM_BOT_TOKEN)

SOURCE_LANGUAGE = "en"
TARGET_LANGUAGE = "ru"

def google_translate(params):
    """
    Translates a phrase using Google Translate API.
    :param params: dictionary containing keys:
        * 'text': string phrase to be translated
        * 'src': source language 2-letter code (e.g. "en")
        * 'dest': destination language 2-letter code (e.g. "ru")
    :return: Translated object with translation result
    """
    translator = Translator()
    translated = translator.translate(params['text'], src=params['src'], dest=params['dest'])
    return translated

def translate(text):
    params = {
        'text': text,
        'src': SOURCE_LANGUAGE,
        'dest': TARGET_LANGUAGE
    }
    translated = google_translate(params)
    if hasattr(translated, "text"):
        return google_translate(params).text
    return "<translation failure>"

def send_message(text, chat_id):
    url = TELEGRAM_REPLY_URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    requests.get(url)

def process_incoming_message(text, chat_id):
    send_message(translate(text), chat_id)

def lambda_handler(event, context):
    message = json.loads(event['body'])
    chat_id = message['message']['chat']['id']
    text = message['message']['text']
    process_incoming_message(text, chat_id)
    return {
        'statusCode': 200
    }
