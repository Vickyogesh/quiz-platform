# common test parameters
import unittest


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
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        conn.execute("TRUNCATE TABLE quiz_answers;")
        conn.execute("TRUNCATE TABLE exam_answers;")
        conn.execute("TRUNCATE TABLE exams;")
        conn.execute("TRUNCATE TABLE answers;")
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        if drop_users:
            conn.execute("TRUNCATE TABLE schools;")
            conn.execute("TRUNCATE TABLE users;")
            conn.execute("TRUNCATE TABLE guest_access;")


def cleanupdb_onTearDown(engine):
    with engine.begin() as conn:
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        conn.execute("TRUNCATE TABLE quiz_answers;")
        conn.execute("TRUNCATE TABLE exam_answers;")
        conn.execute("TRUNCATE TABLE exams;")
        conn.execute("TRUNCATE TABLE answers;")
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        conn.execute("TRUNCATE TABLE guest_access;")
        conn.execute("call aux_create_test_users();")
    engine.dispose()


def _createDigest(nonce, username, passwd):
    import hashlib
    m = hashlib.md5()
    m.update('%s:%s' % (username, passwd))
    ha1 = m.hexdigest()
    m = hashlib.md5()
    m.update('%s:%s' % (nonce, ha1))
    return m.hexdigest()


def createAuthData(nonce, appkey=None, login=None, passwd=None):
    user_login = login or user
    user_pass = passwd or password
    return {
        'nonce': nonce,
        'appid': appkey or app_id,
        'login': user_login,
        'digest': _createDigest(nonce, user_login, user_pass)
    }


# type: admin. school, guest, student
def createAuthFor(type, nonce=123):
    auth = {
        'admin': {'login': 'admin', 'passwd': 'ari09Xsw_'},
        'school': {'login': 'chuck@norris.com', 'passwd': 'boo'},
        'guest': {'login': 'chuck@norris.com-guest', 'passwd': 'guest'},
        'student': {'login': 'testuser', 'passwd': 'testpasswd'}
    }

    user = auth[type]
    return {
        'nonce': nonce,
        'appid': app_id,
        'login': user['login'],
        'digest': _createDigest(nonce, user['login'], user['passwd'])
    }


# See http://stackoverflow.com/questions/12583015/how-can-i-hide-my-stack-frames-in-a-testcase-subclass
__unittest = True


class HttpStatusTest(unittest.TestCase):
    def assertHttp_Unauthorized(self, response):
        if response.status_code != 200:
            raise self.failureException('Non 200 response from server.')

        data = response.json()
        if 'status' not in data or 'description' not in data:
            raise self.failureException('Malformed server error response.')

        if data['status'] == 401:
            if data['description'] != 'Unauthorized.':
                raise self.failureException('Unauthorized, but wrong description.')
        else:
            msg = 'Failed Unauthorized. Actual: %d ' % data['status']
            if 'description' in data:
                msg += data['description']
            raise self.failureException(msg)

    def assertHttp_Forbidden(self, response):
        if response.status_code != 200:
            raise self.failureException('Non 200 response from server.')

        data = response.json()
        if 'status' not in data or 'description' not in data:
            raise self.failureException('Malformed server error response.')

        if data['status'] == 403:
            if data['description'] != 'Forbidden.':
                print data
                raise self.failureException('Forbidden, but wrong description.')
        else:
            msg = 'Failed Forbidden. Actual: %d ' % data['status']
            if 'description' in data:
                msg += data['description']
            raise self.failureException(msg)

    def assertHttp_NotForbidden(self, response):
        if response.status_code != 200:
            raise self.failureException('Non 200 response from server.')

        data = response.json()
        if 'status' not in data:
            raise self.failureException('Malformed server error response.')

        if data['status'] == 403:
            raise self.failureException('Forbidden.')

    def assertHttp_Ok(self, response):
        if response.status_code != 200:
            raise self.failureException('Response status is %d' % response.status_code)

        data = response.json()
        if 'status' not in data:
            raise self.failureException('No status in response.')

        if data['status'] != 200:
            msg = 'Failed OK. Actual: %d ' % data['status']
            if 'description' in data:
                msg += data['description']
            raise self.failureException(msg)
