from difflib import SequenceMatcher
from bson.json_util import dumps
from pymongo import MongoClient
from pymongo import DESCENDING
from pymongo import ASCENDING
from datetime import timedelta
from datetime import datetime
from util.env import db_url
from util import logger

MAX_ENTRIES = 20

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

    def load_modified_news(self, page, sort_by, order, lang):
        order = ASCENDING if order == 'asc' else DESCENDING
        sort_by_field = 'comments_no' if sort_by == 'popular' else 'updated_at' if sort_by == 'time' else 'changes'
        query = {'$where': 'this.created_at<this.updated_at'}
        if lang != 'all':
            query['lang'] = lang
        cursor = self.news.find(query).sort([(sort_by_field, order)]).skip(MAX_ENTRIES * (page - 1)).limit(MAX_ENTRIES)
        count = cursor.count()
        if count > page * MAX_ENTRIES:
            next_url = ''.join(['/api/news?page=', page + 1, '&sort_by=', sort_by, '&order=', order])
        else:
            next_url = None
        return dumps({'news': (list(cursor)), 'meta': {
            "count": MAX_ENTRIES,
            "total_count": count,
            "next": next_url
        }})

    def get_all_urls_older_than(self, interval):
        log.info('getting urls older than %s minutes', interval)
        older_than = datetime.utcnow() - timedelta(seconds=interval * 60)
        return self.news.find({"last_check": {"$lt": older_than}}).distinct('url')
