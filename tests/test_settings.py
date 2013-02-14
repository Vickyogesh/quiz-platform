# common test parameters

app_id = '32bfe1c505d4a2a042bafd53993f10ece3ccddca'
user = 'testuser'
passwd = 'testpasswd'
test_server = 'http://127.0.0.1'
db_uri = 'mysql://quiz:quiz@192.168.56.101/quiz?charset=utf8'


def url(path):
    return test_server + path
