from urllib.parse import parse_qsl
from pymongo import ASCENDING, DESCENDING


ENTRIES = 20


def validate(revision, revisions_count):
    if revision < 0 or revision >= revisions_count:
        raise ValueError("revision index out of bound! " + str(revision))
    return revision


class ArticlesParams(object):
    def __init__(self, from_revision, to_revision):
        self.from_revision = int(from_revision) if from_revision else None
        self.to_revision = int(to_revision) if to_revision else None

    def from_version(self, revisions_count):
        from_revision = max(0, revisions_count - 2) if self.from_revision is None else self.from_revision
        return validate(from_revision, revisions_count)

    def to_version(self, revisions_count):
        to_revision = max(0, revisions_count - 1) if self.to_revision is None else self.to_revision
        return validate(to_revision, revisions_count)

    @classmethod
    def from_req(cls, req):
        params = dict(parse_qsl(req.query_string))
        from_revision = params.get('from_revision', None)
        to_revision = params.get('to_revision', None)
        return cls(from_revision, to_revision)


class NewsParams(object):
    def __init__(self, page, sort_by, order, lang, publisher):
        self.page = page
        self.sort_by = sort_by
        self.order = order
        self.lang = lang
        self.publisher = publisher

    def query(self):
        query_string = {'$where': 'this.created_at<this.updated_at'}
        if self.lang != 'all':
            query_string['lang'] = self.lang
        if self.publisher:
            query_string['publisher'] = self.publisher
        return query_string

    def skipped_pages(self):
        return ENTRIES * (self.page - 1)

    def by_order(self):
        order = ASCENDING if self.order == 'asc' else DESCENDING
        sort_by_field = 'comments_no' if self.sort_by == 'popular' \
            else 'updated_at' if self.sort_by == 'time' else 'changes'
        return [(sort_by_field, order)]

    def get_from(self, db):
        return db.find(self.query()).sort(self.by_order()).skip(self.skipped_pages()).limit(ENTRIES)

    def get_meta(self, cursor):
        count = cursor.count()
        prefix = ''.join(['/api/publisher/', self.publisher, '/news']) if self.publisher else '/api/news'
        next_url = ''.join([prefix, '?page=', str(self.page + 1), '&sort_by=', self.sort_by, '&order=',
                            self.order, '&lang=', self.lang]) if count > self.page * ENTRIES else None
        return {"count": ENTRIES, "total_count": count, "next": next_url}

    @classmethod
    def from_req(cls, req, publisher_code):
        params = dict(parse_qsl(req.query_string))
        page = int(params.get('page', '1'))
        sort_by = params.get('sort_by', 'changes')
        if sort_by not in ['popular', 'time', 'changes']:
            raise ValueError()
        order = params.get('order', 'desc')
        if order not in ['asc', 'desc']:
            raise ValueError()
        lang = params.get('lang', 'all')
        return cls(page, sort_by, order, lang, publisher_code)