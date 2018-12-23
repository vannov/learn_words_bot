import os
import requests
# TODO: revert back to googletrans once this issue is resolved: https://github.com/ssut/py-googletrans/issues/88
from googletrans import Translator
#from py_translator import Translator

WORDS_URL = 'https://wordsapiv1.p.mashape.com/words/'
WORDS_RANDOM = '?hasDetails=typeOf&random=true'

translator = None

def google_translate(params):
    """
    Translates a phrase using Google Translate API.
    :param params: dictionary containing keys:
        * 'text': string phrase to be translated
        * 'src': source language 2-letter code (e.g. "en")
        * 'dest': destination language 2-letter code (e.g. "ru")
    :return: Translated object with translation result
    """
    global translator
    if translator is None:
        translator = Translator()
    translated = translator.translate(params['text'], src=params['src'], dest=params['dest'])
    return translated

def get_word(word=None):
    """
    Gets a random word or specific word description from Words API.
    :param word: specific word. If None or empty string, then a random word is returned.
    :return: dictionary containing keys:
        * 'frequency': {float}
        * 'pronunciation': {dict} {'all': {str}}
        * 'results': {list} [{'definition': {str}, 'partOfSpeech': {str}, 'synonyms': [{str}], 'typeOf': [{str}], 'derivation': [{str}]}]
        * 'syllables': {'count': {int}, 'list': [{str}]}
        * 'word': = {str}
    """
    url = WORDS_URL
    if word is None or word == "":
        url += WORDS_RANDOM

    else:
        url += word
    headers = {'X-Mashape-Key': os.environ['MASHAPE_KEY']}

    r = requests.get(url, headers=headers)
    r.raise_for_status()
    return r.json()
