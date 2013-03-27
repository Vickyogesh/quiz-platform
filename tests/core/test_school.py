# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: create users.
class CoreSchoolTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 2}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check invalid params
    def test_createStudentBad(self):
        # Empty values
        try:
            self.core.createStudent(None, None, None, None, None)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        # Empty values again
        try:
            self.core.createStudent(1, 2, 1, None, 2)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        ### Wrong type of values

        try:
            self.core.createStudent('', '', '', '', 'frd')
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        try:
            self.core.createStudent([], 1, 1, '22', [])
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid parameters.', err)
        err = ''

        # Add user for non-existent school
        try:
            self.core.createStudent('a', 'b', 'v', 'b', 12)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Unknown school.', err)

    # Check normal situation.
    # NOTE: since by default there are 4 users then
    # new user id will be 5.
    def test_normal(self):
        info = self.core.createStudent('name1', 'surnm1', 'login1', 'pass1', 1)
        self.assertEqual(5, info['id'])
        self.assertEqual('name1', info['name'])
        self.assertEqual('surnm1', info['surname'])

    # Check creation of the school with already existent login.
    def test_duplicates(self):
        self.core.createStudent('Bob', 'Marley', 'somelogin', 'pass', 1)

        try:
            self.core.createStudent('Bob', 'Marley', 'somelogin', 'pass', 1)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Already exists.', err)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreSchoolTest))
    return suite

if __name__ == '__main__':
    unittest.main()
