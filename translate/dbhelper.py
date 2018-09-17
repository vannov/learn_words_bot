import os
import psycopg2


TELEGRAM_USERS_TABLE = 'telegram_users'

class DBHelper:

    def __init__(self):
        DATABASE_URL = os.environ['DATABASE_URL']
        self.conn = psycopg2.connect('dbname=' + DATABASE_URL, sslmode='require')
        self.curs = self.conn.cursor()
        pass

    # def commit(self, func):
    #     """ Decorator for methods requiring committing to DB persistent.  """
    #     def func_wrapper(*args, **kwargs):
    #         func(*args, **kwargs)
    #         self.conn.commit()
    #     return func_wrapper

    def create_table(self, name):
        cmd = """CREATE TABLE {0} (
                id int PRIMARY KEY,
                lang_src varchar,
                lang_dest varchar,
                words varchar[]
            );""".format(name)
        self.curs.execute(cmd)
        self.conn.commit()

    def drop_table(self, name):
        cmd = """ DROP TABLE {0};""".format(name)
        self.curs.execute(cmd)
        self.conn.commit()

    def create_user(self, user_id, words=[]):
        data = (user_id, 'en', 'ru', words)
        self.curs.execute(
            'INSERT INTO ' + TELEGRAM_USERS_TABLE +
                ' VALUES (%s, %s, %s, %s)', data);
        self.conn.commit()

    def get_user(self, user_id):
        cmd = """SELECT * FROM {} WHERE id = {}""".format(TELEGRAM_USERS_TABLE, user_id)
        self.curs.execute(cmd)
        return self.curs.fetchone()

    def get_all_users(self):
        cmd = """SELECT * FROM {}""".format(TELEGRAM_USERS_TABLE)
        self.curs.execute(cmd)
        return self.curs.fetchone()

    def insert_word(self, user_id, word):
        user = self.get_user(user_id)
        if user is not None:
            # words = user[3]
            # if word not in words:
            #     words.append(word)
            cmd = """UPDATE {0} SET words = words || '{{1}}' WHERE id = {2};""".format(
                TELEGRAM_USERS_TABLE, word, user_id)
            self.curs.execute(cmd)
            self.conn.commit()
        else:
            self.create_user(user_id, [word])


if __name__ == '__main__':
    # test
    os.environ['DATABASE_URL'] = "botdb"
    db_helper = DBHelper()
    #db_helper.create_table(TELEGRAM_USERS_TABLE)
    #db_helper.create_user(124124, ['lol', 'kek', 'rofl'])
    print('get_all_users: ' + str(db_helper.get_all_users()))

    user_id = 124124
    print('get_user ' + str(user_id) + ' : ' + str(db_helper.get_user(user_id)))


    db_helper.insert_word(user_id=user_id, word='ABC')
    print('get_user ' + str(user_id) + ' : ' + str(db_helper.get_user(user_id)))

    #db_helper.get_user(999)


