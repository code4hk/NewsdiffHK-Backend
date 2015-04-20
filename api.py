from model.models import Publishers
from model.models import Articles
from urllib.parse import parse_qsl
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
        params = dict(parse_qsl(req.query_string))
        try:
            page = int(params.get('page', '1'))
            sort_by = params.get('sort_by', 'changes')
            if sort_by not in ['popular', 'time', 'changes']:
                raise ValueError()
            order = params.get('order', 'desc')
            if order not in ['asc', 'desc']:
                raise ValueError()
            resp.body = self.articles.load_modified_news(
                page, sort_by, order, params.get('lang', 'all'), publisher_code)
        except ValueError:
            raise falcon.HTTPBadRequest('bad request', 'invalid query')


class ArticleResource:
    def __init__(self):
        self.articles = Articles()

    def on_get(self, req, resp, news_id):
        resp.body = self.articles.load_article_history(news_id)

app = falcon.API()
publishers = PublishersResource()
app.add_route('/api/publishers', publishers)
news = NewsResource()
app.add_route('/api/news', news)
app.add_route('/api/publisher/{publisher_code}/news', news)
article = ArticleResource()
app.add_route('/api/news/{news_id}', article)