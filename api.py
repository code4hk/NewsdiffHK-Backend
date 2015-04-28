from model.publisher import Publishers
from model.models import Articles
from model.params import ArticlesParams
from model.params import NewsParams
import falcon


class PublishersResource:
    def __init__(self):
        self.publishers = Publishers()

    def on_get(self, req, resp):
        resp.body = self.publishers.load_publishers()


class NewsResource:
    def __init__(self):
        self.articles = Articles()

    def on_get(self, req, resp, publisher_code=None):
        try:
            resp.body = self.articles.load_modified_news(NewsParams.from_req(req, publisher_code))
        except ValueError as e:
            raise falcon.HTTPBadRequest('bad request', 'invalid query: ' + str(e))


class ArticleResource:
    def __init__(self):
        self.articles = Articles()

    def on_get(self, req, resp, news_id):
        try:
            resp.body = self.articles.load_article_history(news_id, ArticlesParams.from_req(req))
        except ValueError as e:
            raise falcon.HTTPBadRequest('bad request', 'invalid query: ' + str(e))

app = falcon.API()
publishers = PublishersResource()
app.add_route('/api/publishers', publishers)
news = NewsResource()
app.add_route('/api/news', news)
app.add_route('/api/publisher/{publisher_code}/news', news)
article = ArticleResource()
app.add_route('/api/news/{news_id}', article)