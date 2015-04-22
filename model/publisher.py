from bson.json_util import dumps
from pymongo import MongoClient
from util.env import db_url


class Publishers(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.publishers = client.newsdiff.publishers

    def create_publisher_if_not_exists(self, code, name):
        self.publishers.replace_one({'code': code}, {'code': code, 'name': name}, upsert=True)

    def load_publishers(self):
        return dumps(self.publishers.find(projection={'_id': 0}))