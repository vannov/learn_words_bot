import os
import redis
import random
import pickle
from enum import Enum


class Error(Enum):
    """ Error codes returned by methods of class Store """
    SUCCESS = 0
    NO_SAVED_WORDS = 1
    ALREADY_SAVED = 2
    NOT_FOUND = 3

DEFAULT_SOURCE_LANGUAGE = 'en'
DEFAULT_TARGE_LANGUAGE = 'ru'

class Store:
    """ Wrapper around Redis key/value data store. Key is user ID, value is list of words.
        This class expects environment variable REDIS_URL to hold a valid Redis URL. """

    def __init__(self):
        self.r = redis.from_url(os.environ['REDIS_URL'])

    def add_user(self, user_id, src, trg):
        #TODO: implement
        pass

    def set_src_lang(self, user_id, src):
        #TODO
        pass

    def set_dst_lang(self, user_id, dst):
        #TODO
        pass

    def get_user_obj(self, user_id):
        unpacked_object = pickle.loads(self.r.get(user_id))
        if isinstance(unpacked_object, dict):
            return unpacked_object
        else:
            # User not found - return default object
            return {
                'words': [],
                'src': DEFAULT_SOURCE_LANGUAGE,
                'trg': DEFAULT_TARGE_LANGUAGE
            }

    def set_user_obj(self, user_id, obj):
        pickled_object = pickle.dumps(obj)
        self.r.set(user_id, pickled_object)

    # def get_user_words(self, user_id):
    #     unpacked_object = pickle.loads(self.r.get(user_id))
    #     if isinstance(unpacked_object, dict) and 'words' in unpacked_object:
    #         return unpacked_object['words']
    #     else:
    #         return []

    def add_word(self, user_id, word):
        obj = self.get_user_obj(user_id)
        if word not in obj['words']:
            obj['words'].append(word)
            self.set_user_obj(user_id, obj)
            return Error.SUCCESS
        else:
            return Error.ALREADY_SAVED

    def remove_word(self, user_id, word):
        obj = self.get_user_obj(user_id)
        if word in obj['words']:
            obj['words'].remove(word)
            self.set_user_obj(user_id, obj)
            return Error.SUCCESS
        else:
            return Error.NOT_FOUND

    def get_word(self, user_id):
        obj = self.get_user_obj(user_id)
        size = len(obj['words'])
        if size != 0:
            index = random.randint(0, size-1)
            word = obj['words'][index]
            return word
        else:
            # No saved words found for user_id
            return None

    def get_all_words(self, user_id):
        obj = self.get_user_obj(user_id)
        return obj['words']

    def is_saved(self, user_id, word):
        """ Checks if word is saved in the user's list words.
        :param user_id: user ID
        :param word: string word to check
        :return: True if the word is saved, else false
        """
        obj = self.get_user_obj(user_id)
        return word in obj['words']
