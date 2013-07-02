# to use tests_common quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

import requests
import unittest
import json
from sqlalchemy import create_engine
from tests_common import db_uri, url, createAuthFor
from tests_common import cleanupdb_onSetup, cleanupdb_onTearDown
from tests_common import cleanupdb_onSetupAccDb, cleanupdb_onTearDownAccDb


# Test: statistics http requests: /student, /student/<id>,
# /student/<id>/exam, /student/<id>/topicerrors/<id>;
# For more info see tests/core/test_topicstat.py
class HttpStudentStatTest(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(db_uri, echo=False)
        cleanupdb_onSetup(self.engine)
        cleanupdb_onSetupAccDb(self, drop_users=True, add_users=True)

        self.req = requests.Session()

        r = self.req.get(url('/authorize'))

        nonce = r.json()['nonce']
        auth = json.dumps(createAuthFor('student', nonce))
        self.headers = {'content-type': 'application/json'}

        r = self.req.post(url('/authorize'), data=auth, headers=self.headers)
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, r.json()['status'])

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)
        cleanupdb_onTearDownAccDb(self)

    # Check: request student stat.
    def test_student(self):
        r = self.req.get(url('/student'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('exams', data)
        self.assertIn('topics', data)
        self.assertEqual(3, data['student']['id'])

        r = self.req.get(url('/student/me'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('exams', data)
        self.assertIn('topics', data)
        self.assertEqual(3, data['student']['id'])

        r = self.req.get(url('/student/3'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('exams', data)
        self.assertIn('topics', data)
        self.assertEqual(3, data['student']['id'])

    def test_studentExams(self):
        r = self.req.get(url('/student/me/exam'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('exams', data)
        self.assertEqual(3, data['student']['id'])

        r = self.req.get(url('/student/3/exam'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('exams', data)
        self.assertEqual(3, data['student']['id'])

    def test_studentTopicErroros(self):
        r = self.req.get(url('/student/me/topicerrors/1'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('questions', data)
        self.assertEqual(3, data['student']['id'])

        r = self.req.get(url('/student/3/topicerrors/4'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('student', data)
        self.assertIn('questions', data)
        self.assertEqual(3, data['student']['id'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpStudentStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()
