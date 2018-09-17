import os
import redis
import random
from enum import Enum


class Error(Enum):
    """ Error codes returned by methods of class Store """
    SUCCESS = 0
    NO_SAVED_WORDS = 1
    ALREADY_SAVED = 2
    NOT_FOUND = 3


class Store:
    """ Wrapper around Redis key/value data store. Key is user ID, value is list of words.
        This class expects environment variable REDIS_URL to hold a valid Redis URL. """

    def __init__(self):
        self.r = redis.from_url(os.environ['REDIS_URL'])

    def get_word_index(self, user_id, word):
        """ Returns index of word in the user's list of words or -1 if the word is not present. """
        size = self.r.llen(user_id)
        if size != 0:
            words = self.r.lrange(user_id, 0, size - 1)
            words = list(map(lambda x: x.decode("utf-8"), words))
            if word in words:
                return words.index(word)
        return -1

    def add_word(self, user_id, word):
        if self.get_word_index(user_id, word) == -1:
            self.r.lpush(user_id, word)
            return Error.SUCCESS
        else:
            return Error.ALREADY_SAVED

    def remove_word(self, user_id, word):
        index = self.get_word_index(user_id, word)
        if index != -1:
            self.r.lrem(name=user_id, value=word)
            return Error.SUCCESS
        else:
            return Error.NOT_FOUND

    def get_word(self, user_id):
        size = self.r.llen(user_id)
        if size != 0:
            index = random.randint(0, size-1)
            word = self.r.lindex(user_id, index)
            return word.decode("utf-8")
        else:
            # No saved words found for user_id
            return None

    def get_all_words(self, user_id):
        size = self.r.llen(user_id)
        if size != 0:
            words = self.r.lrange(user_id, 0, size - 1)
            words = list(map(lambda x: x.decode("utf-8"), words))
            return words
        else:
            # No saved words
            return None


if __name__ == '__main__':
    # test
    os.environ['REDIS_URL'] = '' # set Redis URL
    s = Store()
    user_id = 0 # set user ID
    print('ALL WORDS: ' + str(s.get_all_words(user_id)))
