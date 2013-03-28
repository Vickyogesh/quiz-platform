# common test parameters

app_id = '32bfe1c505d4a2a042bafd53993f10ece3ccddca'
user = 'testuser'
password = 'testpasswd'
db_uri = 'mysql://quiz:quiz@192.168.56.101/quiz?charset=utf8'
test_server = 'http://127.0.0.1/v1'
#test_server = 'http://quizplatformtest-editricetoni.rhcloud.com/v1'


def url(path):
    return test_server + path


def cleanupdb_onSetup(engine, drop_users=False):
    with engine.begin() as conn:
        conn.execute("TRUNCATE TABLE quiz_answers;")
        conn.execute("TRUNCATE TABLE exam_answers;")
        conn.execute("TRUNCATE TABLE exams;")
        conn.execute("TRUNCATE TABLE errors;")
        conn.execute("TRUNCATE TABLE topics_stat;")
        if drop_users:
            conn.execute("TRUNCATE TABLE schools;")
            conn.execute("TRUNCATE TABLE users;")
            conn.execute("TRUNCATE TABLE guest_access;")


def cleanupdb_onTearDown(engine):
    with engine.begin() as conn:
        conn.execute("TRUNCATE TABLE quiz_answers;")
        conn.execute("TRUNCATE TABLE exam_answers;")
        conn.execute("TRUNCATE TABLE exams;")
        conn.execute("TRUNCATE TABLE errors;")
        conn.execute("TRUNCATE TABLE topics_stat;")
        conn.execute("TRUNCATE TABLE guest_access;")
        conn.execute("call aux_create_test_users();")
    engine.dispose()


def _getNonce(header):
    return header[16:-1]


def _createHeader(nonce, app_id, username, digest):
    fmt = 'QuizAuth nonce="{0}", appid="{1}", username="{2}", digest="{3}"'
    return fmt.format(nonce, app_id, username, digest)


def _createDigest(nonce, username, passwd):
    import hashlib
    m = hashlib.md5()
    m.update('%s:%s' % (username, passwd))
    ha1 = m.hexdigest()
    m = hashlib.md5()
    m.update('%s:%s' % (nonce, ha1))
    return m.hexdigest()


def createAuthHeader(wwwheader, appkey=None, login=None, passwd=None):
    app = appkey or app_id
    user_login = login or user
    user_pass = passwd or password

    nonce = _getNonce(wwwheader)
    digest = _createDigest(nonce, user_login, user_pass)
    return _createHeader(nonce, app, user_login, digest)
