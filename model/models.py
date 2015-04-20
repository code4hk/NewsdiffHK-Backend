from difflib import SequenceMatcher
from bson.objectid import ObjectId
from bson.json_util import dumps
from pymongo import MongoClient
from pymongo import DESCENDING
from pymongo import ASCENDING
from datetime import timedelta
from datetime import datetime
from util.env import db_url
from util import logger

ENTRIES = 20

log = logger.get(__name__)


class Publishers(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.publishers = client.newsdiff.publishers

    def create_publisher_if_not_exists(self, code, name):
        self.publishers.replace_one({'code': code}, {'code': code, 'name': name}, upsert=True)

    def load_publishers(self):
        return dumps(self.publishers.find(projection={'_id': 0}))


def sequence(date, title, body):
    return date + title + body


def matcher(base_revision, date, title, body):
    return SequenceMatcher(None,
                           sequence(
                               base_revision['published_at'],
                               base_revision['title'],
                               base_revision['body']),
                           sequence(date, title, body),
                           False)


def by_order(order, sort_by):
    order = ASCENDING if order == 'asc' else DESCENDING
    sort_by_field = 'comments_no' if sort_by == 'popular' else 'updated_at' if sort_by == 'time' else 'changes'
    return [(sort_by_field, order)]


def get_meta(cursor, order, page, sort_by, lang, publisher):
    count = cursor.count()
    prefix = ''.join(['/api/publisher/', publisher, '/news']) if publisher else '/api/news'
    next_url = ''.join([prefix, '?page=', str(page + 1), '&sort_by=', sort_by, '&order=', order, '&lang=', lang]) \
        if count > page * ENTRIES else None
    meta = {"count": ENTRIES, "total_count": count, "next": next_url}
    return meta


def diff_string(original, revision):
    if not original or not revision:
        return None
    parts = []
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, original, revision, False).get_opcodes():
        if tag == 'replace':
            parts.append(''.join(['<o>', original[i1:i2], '</o>']))
            parts.append(''.join(['<c>', revision[j1:j2], '</c>']))
        elif tag == 'insert':
            parts.append(''.join(['<c>', revision[j1:j2], '</c>']))
        elif tag == 'delete':
            parts.append(''.join(['<o>', original[i1:i2], '</o>']))
        elif tag == 'equal':
            parts.append(original[i1:i2])
    return ''.join(parts)


class Articles(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.news = client.newsdiff.news
        self.revisions = client.newsdiff.revisions

    def save_entry(self, publisher, url, date, title, body, lang):
        news_cursor = self.news.find({"url": url})
        if news_cursor.count() == 0:
            log.info('new entry: %s', url)
            self.new_entry(publisher, url, date, title, body, lang)
        else:
            nid = news_cursor[0]['_id']
            revision_cursor = self.revisions.find({'nid': str(nid)})
            first_version = revision_cursor[0]
            last_revision = revision_cursor[revision_cursor.count() - 1]
            ratio = matcher(last_revision, date, title, body).ratio()
            if ratio < 1:
                log.info('new entry version: %s', url)
                overall_ratio = matcher(first_version, date, title, body).ratio()
                self.update_news_entry(nid, title, 1 - overall_ratio)
                self.new_revision(nid, revision_cursor.count(), title, date, body)
            else:
                log.debug('entry not modified: %s', url)
                self.update_last_check_time(nid)

    def new_entry(self, publisher, url, date, title, body, lang):
        now = datetime.utcnow()
        news_entry = {"url": url,
                      "title": title,
                      "publisher": publisher,
                      "comments_no": 0,
                      "changes": 0,
                      "lang": lang,
                      "created_at": now,
                      "updated_at": now,
                      "last_check": now
                      }
        result = self.news.insert_one(news_entry)
        self.new_revision(result.inserted_id, 0, title, date, body)

    def new_revision(self, nid, version, title, date, body):
        revision_entry = {"nid": str(nid),
                          "version": version,
                          "title": title,
                          "published_at": date,
                          "body": body,
                          "archive_time": datetime.utcnow()
                          }
        self.revisions.insert_one(revision_entry)

    def update_news_entry(self, nid, title, changes):
        now = datetime.utcnow()
        self.news.update_one({'_id': nid}, {'$set': {
            'title': title, 'changes': changes, "updated_at": now, "last_check": now}})

    def update_last_check_time(self, nid):
        self.news.update_one({"_id": nid}, {'$set': {"last_check": datetime.utcnow()}})

    def load_modified_news(self, page, sort_by, order, lang, publisher):
        cursor = self.query(lang, publisher).sort(by_order(order, sort_by)).skip(ENTRIES * (page - 1)).limit(ENTRIES)
        return dumps({'news': (list(cursor)), 'meta': (get_meta(cursor, order, page, sort_by, lang, publisher))})

    def query(self, lang, publisher_code):
        query = {'$where': 'this.created_at<this.updated_at'}
        if lang != 'all':
            query['lang'] = lang
        if publisher_code:
            query['publisher'] = publisher_code
        return self.news.find(query)

    def get_all_urls_older_than(self, interval):
        log.info('getting urls older than %s minutes', interval)
        older_than = datetime.utcnow() - timedelta(seconds=interval * 60)
        return self.news.find({"last_check": {"$lt": older_than}}).distinct('url')

    def load_article_history(self, news_id):
        news = self.news.find({'_id': ObjectId(news_id)})[0]
        revisions = list(self.revisions.find({'nid': news_id}, projection={'_id': 0, 'nid': 0}))
        prev = None
        for item in revisions:
            body = item['body']
            item['content'] = diff_string(prev, body)
            prev = body
        news['revisions'] = revisions
        return dumps(news)



