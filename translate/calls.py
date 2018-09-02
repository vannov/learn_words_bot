import os
import requests
from googletrans import Translator

#GOOGLE_TRANSLATE_URL = 'https://translation.googleapis.com/language/translate/v2'
WORDS_URL = 'https://wordsapiv1.p.mashape.com/words/'
WORDS_RANDOM = '?hasDetails=typeOf&random=true'


def google_translate(params):
    """
    Translates a phrase using Google Translate API.
    :param params: dictionary containing keys:
        * 'text': string phrase to be translated
        * 'src': source language 2-letter code (e.g. "en")
        * 'dest': destination language 2-letter code (e.g. "ru")
    :return: string translation result
    """
    translator = Translator()
    translated = translator.translate(params['text'], src=params['src'], dest=params['dest'])
    return translated.text

def get_word(word):
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
