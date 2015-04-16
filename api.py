from model.models import Publishers
import falcon
import json


class PublishersResource:
    def __init__(self):
        self.publishers = Publishers()

    def on_get(self, req, resp):
        resp.body = json.dumps(self.publishers.load_publishers())

app = falcon.API()
publishers = PublishersResource()
app.add_route('/api/publishers', publishers)