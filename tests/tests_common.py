# common test parameters
import hashlib
import unittest
from sqlalchemy import create_engine, MetaData, text

app_id = '32bfe1c505d4a2a042bafd53993f10ece3ccddca'
user = 'testuser'
password = 'testpasswd'
db_uri = 'mysql://quiz:quiz@192.168.56.101/quiz?charset=utf8'
test_server = 'http://127.0.0.1/v1'
#test_server = 'http://quizplatformtest-editricetoni.rhcloud.com/v1'

acc_db_uri = 'mysql://quiz:quiz@192.168.56.101/accounts'


def url(path):
    return test_server + path


def cleanupdb_onSetup(engine, drop_users=False):
    with engine.begin() as conn:
        conn.execute("TRUNCATE TABLE user_progress_snapshot;")
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        conn.execute("TRUNCATE TABLE quiz_answers;")
        conn.execute("TRUNCATE TABLE exam_answers;")
        conn.execute("TRUNCATE TABLE exams;")
        conn.execute("TRUNCATE TABLE answers;")
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        if drop_users:
            conn.execute("TRUNCATE TABLE users;")
            conn.execute("TRUNCATE TABLE guest_access;")


def cleanupdb_onTearDown(engine):
    with engine.begin() as conn:
        conn.execute("TRUNCATE TABLE user_progress_snapshot;")
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        conn.execute("TRUNCATE TABLE quiz_answers;")
        conn.execute("TRUNCATE TABLE exam_answers;")
        conn.execute("TRUNCATE TABLE exams;")
        conn.execute("TRUNCATE TABLE answers;")
        conn.execute("TRUNCATE TABLE topic_err_current;")
        conn.execute("TRUNCATE TABLE topic_err_snapshot;")
        conn.execute("TRUNCATE TABLE guest_access;")
        conn.execute("TRUNCATE TABLE users;")
        #conn.execute("DELETE FROM users WHERE school_id=1")
        conn.execute("INSERT INTO users VALUES(1, 'guest', 1, UTC_TIMESTAMP(), -1)")
        conn.execute("INSERT INTO users VALUES(2, 'guest', 2, UTC_TIMESTAMP(), -1)")
        conn.execute("INSERT INTO users VALUES(3, 'student', 1, UTC_TIMESTAMP(), -1)")
        conn.execute("INSERT INTO users VALUES(4, 'student', 1, UTC_TIMESTAMP(), -1)")

    engine.dispose()


def cleanupdb_onSetupAccDb(tst, drop_users=False, add_users=False):
    tst.acc_engine = create_engine(acc_db_uri, echo=False)
    tst.acc_meta = MetaData()
    tst.acc_meta.reflect(tst.acc_engine)
    tst.acc_schools = tst.acc_meta.tables['acc_schools']
    tst.acc_users = tst.acc_meta.tables['acc_users']
    if drop_users:
        tst.acc_engine.execute("DELETE FROM acc_users")
        tst.acc_engine.execute("DELETE FROM acc_schools")
        tst.acc_engine.execute("ALTER TABLE acc_schools AUTO_INCREMENT=1")
        tst.acc_engine.execute("ALTER TABLE acc_users AUTO_INCREMENT=1")
    if add_users:
        tst.acc_engine.execute(tst.acc_schools.insert().values(
            name='Chuck Norris School',
            login='chuck@norris.com',
            passwd=_pwd('chuck@norris.com', 'boo')))
        tst.acc_engine.execute(tst.acc_schools.insert().values(
            name='school2',
            login='school2',
            passwd=_pwd('school2', 'boo')))
        tst.acc_engine.execute(tst.acc_users.insert().values(
            name='Test',
            surname='User',
            login='testuser',
            passwd=_pwd('testuser', 'testpasswd'),
            school_id=1))
        tst.acc_engine.execute(tst.acc_users.insert().values(
            name='Test',
            surname='User2',
            login='testuser2',
            passwd=_pwd('testuser2', 'testpasswd'),
            school_id=1))


def cleanupdb_onTearDownAccDb(tst):
    tst.acc_engine.execute("DELETE FROM acc_users")
    tst.acc_engine.execute("DELETE FROM acc_schools")
    tst.acc_engine.execute("ALTER TABLE acc_schools AUTO_INCREMENT=1")
    tst.acc_engine.execute("ALTER TABLE acc_users AUTO_INCREMENT=1")
    tst.acc_engine.execute(tst.acc_schools.insert().values(
        name='Chuck Norris School',
        login='chuck@norris.com',
        passwd=_pwd('chuck@norris.com', 'boo')))
    tst.acc_engine.execute(tst.acc_schools.insert().values(
        name='school2',
        login='school2',
        passwd=_pwd('school2', 'boo')))
    tst.acc_engine.execute(tst.acc_users.insert().values(
        name='Test',
        surname='User',
        login='testuser',
        passwd=_pwd('testuser', 'testpasswd'),
        school_id=1))
    tst.acc_engine.dispose()


def _pwd(username, passwd):
    m = hashlib.md5()
    m.update('%s:%s' % (username, passwd))
    return m.hexdigest()


def _createDigest(nonce, username, passwd):
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
        'admin': {'login': 'admin', 'passwd': 's=myA{xOYQ.(Vbgx26'},
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

        if data['status'] == 403:
            return

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
