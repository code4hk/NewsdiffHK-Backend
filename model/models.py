from difflib import SequenceMatcher
from bson.objectid import ObjectId
from bson.json_util import dumps
from model.content import Content
from pymongo import MongoClient
from datetime import timedelta
from datetime import datetime
from util.env import db_url
from util import logger


log = logger.get(__name__)


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

    def save_entry(self, article, url):
        content = Content.from_article(article)
        news_cursor = self.news.find({"url": url})
        if news_cursor.count() == 0:
            log.info('new entry: %s', url)
            self.new_entry(article.code, url, article.lang, content)
        else:
            nid = news_cursor[0]['_id']
            revision_cursor = self.revisions.find({'nid': str(nid)})
            first_version = revision_cursor[0]
            last_revision = revision_cursor[revision_cursor.count() - 1]
            if content.change_ratio(last_revision) > 0:
                log.info('new entry version: %s', url)
                self.update_news_entry(nid, content.title, content.change_ratio(first_version))
                self.new_revision(nid, revision_cursor.count(), content)
            else:
                log.debug('entry not modified: %s', url)
                self.update_last_check_time(nid)

    def new_entry(self, publisher, url, lang, content):
        now = datetime.utcnow()
        news_entry = {"url": url,
                      "title": content.title,
                      "publisher": publisher,
                      "comments_no": 0,
                      "changes": 0,
                      "lang": lang,
                      "created_at": now,
                      "updated_at": now,
                      "last_check": now
                      }
        result = self.news.insert_one(news_entry)
        self.new_revision(result.inserted_id, 0, content)

    def new_revision(self, nid, version, content):
        revision_entry = {"nid": str(nid),
                          "version": version,
                          "title": content.title,
                          "published_at": content.date,
                          "body": content.body,
                          "archive_time": datetime.utcnow()
                          }
        self.revisions.insert_one(revision_entry)

    def update_news_entry(self, nid, title, changes):
        now = datetime.utcnow()
        self.news.update_one({'_id': nid}, {'$set': {
            'title': title, 'changes': changes, "updated_at": now, "last_check": now}})

    def update_last_check_time(self, nid):
        self.news.update_one({"_id": nid}, {'$set': {"last_check": datetime.utcnow()}})

    def load_modified_news(self, params):
        cursor = params.get_from(self.news)
        return dumps({'news': (list(cursor)), 'meta': (params.get_meta(cursor))})

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
