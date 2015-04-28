from difflib import SequenceMatcher
from bson.objectid import ObjectId
from bson.errors import InvalidId
from bson.json_util import dumps
from pymongo import MongoClient
from util.env import db_url
from util import logger


log = logger.get(__name__)


def diff(before, after):
    before_parts = []
    after_parts = []
    before_content = before['body']
    after_content = after['body']
    for tag, i1, i2, j1, j2 in SequenceMatcher(None, before_content, after_content, False).get_opcodes():
        if tag == 'replace' or tag == 'delete':
            before_parts.append(''.join(['<o>', before_content[i1:i2], '</o>']))
        else:
            before_parts.append(before_content[i1:i2])
        if tag == 'replace' or tag == 'insert':
            after_parts.append(''.join(['<c>', after_content[j1:j2], '</c>']))
        else:
            after_parts.append(after_content[j1:j2])
    before['content'] = ''.join(before_parts)
    after['content'] = ''.join(after_parts)
    return {'from': before, 'to': after}


class Articles(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.news = client.newsdiff.news
        self.revisions = client.newsdiff.revisions

    def load_modified_news(self, params):
        cursor = params.get_from(self.news)
        return dumps({'news': (list(cursor)), 'meta': (params.get_meta(cursor))})

    def load_article_history(self, news_id, params):
        try:
            news = self.news.find({'_id': ObjectId(news_id)})[0]
        except InvalidId as e:
            raise ValueError(e)
        revisions = list(self.revisions.find({'nid': news_id}, projection={'_id': 0, 'nid': 0}))
        count = len(revisions)
        news['total_revisions'] = count
        news['revisions'] = diff(revisions[params.from_version(count)], revisions[params.to_version(count)])
        return dumps(news)
