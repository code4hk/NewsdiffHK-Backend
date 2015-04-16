from pymongo import DESCENDING
from pymongo import MongoClient
from datetime import timedelta
from datetime import datetime
from util.env import db_url
from util import logger


log = logger.get(__name__)


class Publishers(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.publishers = client.newsdiff.publishers

    def create_publisher_if_not_exists(self, code, name):
        self.publishers.replace_one({'code': code}, {'code': code, 'name': name}, upsert=True)

    def load_publishers(self):
        return list(self.publishers.find(projection={'_id': 0}))


class Articles(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.articles = client.newsdiff.articles

    def save_revision(self, publisher, url, date, title, body):
        cursor = self.articles.find({"url": url})
        count = cursor.count()
        if count == 0:
            log.info('new entry: %s', url)
            self.save(publisher, url, 0, date, title, body)
        else:
            last_revision = cursor[count - 1]
            if last_revision["published_at"] != date or last_revision["title"] != title or last_revision["body"] != body:
                log.info('new entry version: %s', url)
                self.save(publisher, url, count, date, title, body)
            else:
                log.debug('entry not modified: %s', url)
                self.update_last_check_time(url)

    def save(self, publisher, url, version, date, title, body):
        entry = {"url": url,
                 "publisher": publisher,
                 "version": version,
                 "published_at": date,
                 "title": title,
                 "body": body,
                 "created_at": datetime.utcnow(),
                 "last_check": datetime.utcnow()
                 }
        self.articles.insert_one(entry)

    def update_last_check_time(self, url):
        self.articles.update_many({"url": url}, {'$set': {"last_check": datetime.utcnow()}})

    def load_modified_url(self):
        cursor = self.articles.aggregate([
            {"$group": {"_id": "$url", "count": {"$sum": 1}}},
            {"$sort": {"count": -1}},
            {"$match": {"count": {"$gt": 1}}}
        ])
        modified_url = [i['_id'] for i in cursor]
        log.info('loaded %s modified urls', len(modified_url))
        return modified_url

    def load_modified_news(self):
        return list(self.articles.find({"url": {"$in": self.load_modified_url()}}).sort([('url', DESCENDING)]))[:100]

    def get_all_urls_older_than(self, interval):
        log.info('getting urls older than %s minutes', interval)
        older_than = datetime.utcnow() - timedelta(seconds=interval * 60)
        return self.articles.find({"last_check": {"$lt": older_than}}).distinct('url')
