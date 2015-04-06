from util import logger
import datetime
import sqlite3


log = logger.get(__name__)


class Articles(object):
    def __init__(self):
        self.conn = sqlite3.connect('articles.db')
        self.create_table_if_not_exist()

    def save_revision(self, url, date, title, body):
        cur = self.conn.cursor()
        cur.execute('select * from article where url = ?', (url,))
        rev_list = cur.fetchall()
        if len(rev_list) == 0:
            log.info('new entry: %s', url)
            self.save(url, 0, date, title, body)
        else:
            last_revision = rev_list[-1]
            if last_revision[2] != date or last_revision[3] != title or last_revision[4] != body:
                log.info('new entry version: %s', url)
                self.save(url, len(rev_list), date, title, body)
            else:
                log.debug('entry not modified: %s', url)

    def save(self, url, version, date, title, body):
        self.conn.execute('insert into article values (?, ?, ?, ?, ?, ?)',
                          (url, version, date, title, body, datetime.datetime.now()))
        self.conn.commit()

    def create_table_if_not_exist(self):
        self.conn.execute('''create table if not exists article
        (url text, version integer, date text, title text, body text, capture_time timestamp)''')
        self.conn.execute('create unique index if not exists url_version on article(url, version)')

    def get_all_urls(self):
        cur = self.conn.cursor()
        cur.execute('select distinct url from article')
        return [x[0] for x in cur.fetchall()]