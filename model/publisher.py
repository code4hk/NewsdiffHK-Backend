from bson.json_util import dumps
from pymongo import MongoClient
from util.env import db_url


class Publishers(object):
    def __init__(self):
        client = MongoClient(db_url())
        self.publishers = client.newsdiff.publishers

    def load_publishers(self):
        return dumps(self.publishers.find(projection={'_id': 0}))