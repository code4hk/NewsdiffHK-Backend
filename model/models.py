from util.env import data_dir
from datetime import datetime
from util import logger
import sqlite3


log = logger.get(__name__)


class Articles(object):
    def __init__(self):
        self.conn = sqlite3.connect(data_dir() + '/articles.db')
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
                self.update_last_check_time(url)

    def save(self, url, version, date, title, body):
        self.conn.execute('insert into article values (?, ?, ?, ?, ?, ?, ?)',
                          (url, version, date, title, body, datetime.now(), datetime.now()))
        self.conn.commit()

    def update_last_check_time(self, url):
        self.conn.execute('update article set last_check = ? where url = ?', (datetime.now(), url,))
        self.conn.commit()

    def load_modified_url(self):
        return self.conn.execute(
            'select url from article group by url having count(*) > 1').fetchall()

    def load_modified_news(self):
        return self.conn.execute(
            '''select * from article where url in
            (select url from article group by url having count(*) > 1)
            order by url''').fetchall()

    def create_table_if_not_exist(self):
        self.conn.execute('''create table if not exists article
        (url text, version integer, date text, title text, body text, capture_time timestamp,
        last_check timestamp default '1901-01-01')''')
        self.conn.execute('create unique index if not exists url_version on article(url, version)')

    def get_all_urls_older_than(self, interval):
        urls = self.conn.execute(''' select distinct url from article
        where strftime('%s','now') - strftime('%s',last_check) > ? ''', (interval * 60,)).fetchall()
        return [x[0] for x in urls]
