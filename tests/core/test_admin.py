# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
import hashlib
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: create school.
class CoreAdminTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 2}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine, drop_users=True)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check invalid params
    def test_createSchoolBad(self):
        # Empty values
        try:
            self.core.createSchool(None, None, None)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        # Empty values again
        try:
            self.core.createSchool(1, 2, None)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        ### Wrong type of values

        try:
            self.core.createSchool('', '', '')
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        try:
            self.core.createSchool(1, 1, '22')
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)

    def _create_digest(self, username):
        m = hashlib.md5()
        m.update('%s:guest' % username)
        return m.hexdigest()

    # Check normal situation.
    def test_normal(self):
        info = self.core.createSchool('someschool', 'somelogin', 'pass')
        self.assertEqual(1, info['id'])

        res = self.engine.execute('SELECT * from schools')
        res = res.fetchone()
        self.assertEqual(1, res['id'])
        self.assertEqual('someschool', res['name'])
        self.assertEqual('somelogin', res['login'])

        # School guest must be created additionally to the school.
        res = self.engine.execute('SELECT * from users WHERE type="guest"')
        res = res.fetchone()
        self.assertEqual(1, res['id'])
        self.assertEqual(1, res['school_id'])
        self.assertEqual('someschool', res['name'])
        self.assertEqual('', res['surname'])
        self.assertEqual('guest', res['type'])
        self.assertEqual('somelogin-guest', res['login'])
        pwd = self._create_digest('somelogin-guest')
        self.assertEqual(pwd, res['passwd'])

    # Check: creation of the school with already existent login.
    def test_duplicates(self):
        self.core.createSchool('someschool', 'somelogin', 'pass')
        try:
            self.core.createSchool('someschool', 'somelogin', 'pass')
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Already exists.', err)

    # Check: get list of schools.
    def test_schoolList(self):
        # Test empty
        info = self.core.getSchoolList()
        self.assertEqual(0, len(info['schools']))

        # Check list
        self.core.createSchool('someschool1', 'somelogin1', 'pass')
        self.core.createSchool('someschool2', 'somelogin2', 'pass')
        self.core.createSchool('someschool3', 'somelogin3', 'pass')

        info = self.core.getSchoolList()
        info = info['schools']
        self.assertEqual(3, len(info))

        school = info[0]
        self.assertEqual(1, school['id'])
        self.assertEqual('someschool1', school['name'])
        self.assertEqual('somelogin1', school['login'])

        # NOTE: next schools will have ids = 3, 5
        # since there are also guest users.
        school = info[1]
        self.assertEqual(2, school['id'])
        self.assertEqual('someschool2', school['name'])
        self.assertEqual('somelogin2', school['login'])

        school = info[2]
        self.assertEqual(3, school['id'])
        self.assertEqual('someschool3', school['name'])
        self.assertEqual('somelogin3', school['login'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreAdminTest))
    return suite

if __name__ == '__main__':
    unittest.main()
