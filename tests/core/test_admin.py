# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: generate exam, save exam, exam's errors counting.
class AdminTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 2}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        self.engine.execute("TRUNCATE TABLE users;")
        self.engine.execute("TRUNCATE TABLE guest_access;")

    def tearDown(self):
        self.engine.execute("TRUNCATE TABLE users;")
        self.engine.execute("TRUNCATE TABLE guest_access;")

    # Check invalid params
    def test_createSchoolBad(self):
        # Empty values
        try:
            self.core.createSchool(None, None, None)
        except QuizCoreError as e:
            msg = e.message
        self.assertEqual('Invalid parameters.', msg)
        msg = ''

        # Empty values again
        try:
            self.core.createSchool(1, 2, None)
        except QuizCoreError as e:
            msg = e.message
        self.assertEqual('Invalid parameters.', msg)
        msg = ''

        ### Wrong type of values

        try:
            self.core.createSchool('', '', '')
        except QuizCoreError as e:
            msg = e.message
        self.assertEqual('Invalid parameters.', msg)
        msg = ''

        try:
            self.core.createSchool(1, 1, '22')
        except QuizCoreError as e:
            msg = e.message
        self.assertEqual('Invalid parameters.', msg)

    # Check normal situation.
    def test_normal(self):
        info = self.core.createSchool('someschool', 'somelogin', 'pass')
        self.assertEqual(1, info['id'])

    # Check creation of the school with already existent login.
    def test_duplicates(self):
        self.core.createSchool('someschool', 'somelogin', 'pass')

        try:
            self.core.createSchool('someschool', 'somelogin', 'pass')
        except QuizCoreError as e:
            msg = e.message
        self.assertEqual('Already exists.', msg)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AdminTest))
    return suite

if __name__ == '__main__':
    unittest.main()
