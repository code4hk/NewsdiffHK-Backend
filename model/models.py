from difflib import SequenceMatcher
from bson.objectid import ObjectId
from bson.json_util import dumps
from pymongo import MongoClient
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

    def load_modified_news(self, params):
        cursor = params.get_from(self.news)
        return dumps({'news': (list(cursor)), 'meta': (params.get_meta(cursor))})

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
