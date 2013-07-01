# common test parameters
import hashlib
import unittest
from datetime import date
from sqlalchemy import create_engine, MetaData

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
    engine.execute("TRUNCATE TABLE user_progress_snapshot;")
    engine.execute("TRUNCATE TABLE topic_err_current;")
    engine.execute("TRUNCATE TABLE topic_err_snapshot;")
    engine.execute("TRUNCATE TABLE quiz_answers;")
    engine.execute("TRUNCATE TABLE exam_answers;")
    engine.execute("TRUNCATE TABLE exams;")
    engine.execute("TRUNCATE TABLE answers;")
    engine.execute("TRUNCATE TABLE school_topic_err;")
    engine.execute("TRUNCATE TABLE school_topic_err_snapshot;")
    engine.execute("TRUNCATE TABLE school_stat_cache;")
    if drop_users:
        engine.execute("TRUNCATE TABLE users;")
        engine.execute("TRUNCATE TABLE guest_access;")
        engine.execute("TRUNCATE TABLE guest_access_snapshot;")


def cleanupdb_onTearDown(engine):
    engine.execute("TRUNCATE TABLE user_progress_snapshot;")
    engine.execute("TRUNCATE TABLE topic_err_current;")
    engine.execute("TRUNCATE TABLE topic_err_snapshot;")
    engine.execute("TRUNCATE TABLE quiz_answers;")
    engine.execute("TRUNCATE TABLE exam_answers;")
    engine.execute("TRUNCATE TABLE exams;")
    engine.execute("TRUNCATE TABLE answers;")
    engine.execute("TRUNCATE TABLE guest_access;")
    engine.execute("TRUNCATE TABLE guest_access_snapshot;")
    engine.execute("TRUNCATE TABLE users;")
    engine.execute("TRUNCATE TABLE school_topic_err;")
    engine.execute("TRUNCATE TABLE school_topic_err_snapshot;")
    engine.execute("TRUNCATE TABLE school_stat_cache;")
    engine.execute("INSERT INTO users VALUES(1, 'guest', 1, 1, UTC_TIMESTAMP(), -1)")
    engine.execute("INSERT INTO users VALUES(2, 'guest', 1, 2, UTC_TIMESTAMP(), -1)")
    engine.execute("INSERT INTO users VALUES(3, 'student', 1, 1, UTC_TIMESTAMP(), -1)")
    engine.execute("INSERT INTO users VALUES(3, 'student', 2, 1, UTC_TIMESTAMP(), -1)")
    engine.execute("INSERT INTO users VALUES(4, 'student', 1, 1, UTC_TIMESTAMP(), -1)")
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
            access_quiz_b=date(2050, 01, 01),
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


def createAuthData(nonce, appkey=None, login=None, passwd=None,
                   quiz_type='quiz_b'):
    user_login = login or user
    user_pass = passwd or password
    return {
        'nonce': nonce,
        'appid': appkey or app_id,
        'login': user_login,
        'quiz_type': quiz_type,
        'digest': _createDigest(nonce, user_login, user_pass)
    }


# type: admin. school, guest, student
def createAuthFor(type, nonce=123, quiz_type='quiz_b'):
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
        'quiz_type': quiz_type,
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
        if 'status' not in data:
            raise self.failureException('Malformed server error response.')

        if data['status'] == 403:
            if 'description' not in data:
                raise self.failureException('Malformed server error response.')
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
