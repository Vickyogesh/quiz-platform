import sys
import re
from texttable import Texttable


def api_calls(f):
    for line in f:
        if not line.startswith('[pid:'):
            continue
        lst = line.split(' ')
        i = 17 if lst[16][-1] == ']' else 16
        yield lst[i:]


class UrlMatcher(object):
    def __init__(self):
        self.tests = []

    def add(self, rx, short_url):
        r = re.compile(rx)
        self.tests.append((r, short_url))

    def shortUrl(self, url):
        for test in self.tests:
            if test[0].match(url):
                return test[1]
        return url


matcher = UrlMatcher()
matcher.add('^/v1/student/(me|[0-9]+)$', '/v1/student/XX')
matcher.add('^/v1/student/(me|[0-9]+)/topicerrors/[0-9]+$',
            '/v1/student/XX/topicerrors/XX')
matcher.add('^/v1/student/[0-9]+/exam$', '/v1/student/XX/exam')
matcher.add('^/v1/school/(me|[0-9]+)/student/[0-9]+$',
            '/v1/school/XX/student/XX')


def get_uri(uri):
    i = uri.find('?')
    if i != -1:
        uri = uri[:i]

    if uri.startswith('/v1/quiz'):
        uri = '/v1/quiz'
    elif uri.startswith('/v1/exam'):
        uri = '/v1/exam'

    uri = matcher.shortUrl(uri)
    return uri


def median(lst):
    s = sorted(lst)
    l = len(lst)

    if l % 2 == 0:
        return s[l / 2]
    else:
        return round((s[l / 2] + s[l / 2 - 1]) / 2.0)


f = open(sys.argv[1], 'r')
map_ = {}
for line in api_calls(f):
    http_type = line[0]
    uri = get_uri(line[1])
    timeout = int(line[7])
    k = (http_type, uri)

    info = map_.get(k)
    if info:
        info.append(timeout)
    else:
        map_[k] = [timeout]

items = []
for k, v in map_.iteritems():
    items.append((k[0], k[1], median(v), sum(v) / len(v),
                 min(v), max(v)))


table = Texttable(100)
table.set_deco(Texttable.HEADER)
table.set_cols_align(["l", "l", "r", 'r', 'r', 'r'])
table.header(["method", "URL", "median", 'avg', 'min', 'max'])


def cmp_(a, b):
    return cmp(a[1], b[1])

table.add_rows(sorted(items, cmp=cmp_), header=False)
print table.draw()
