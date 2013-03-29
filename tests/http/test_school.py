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


# Test: school http requests: /school/<uid:id>/students,
# /school/<uid:id>/newstudent
# For more info see tests/core/test_school.py
class HttpSchoolTest(unittest.TestCase):
    def setUp(self):
        self.req = requests.Session()

        r = self.req.get(url('/authorize'))

        nonce = r.json()['nonce']
        auth = json.dumps(createAuthFor('school', nonce))
        self.headers = {'content-type': 'application/json'}

        r = self.req.post(url('/authorize'), data=auth, headers=self.headers)
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, r.json()['status'])

        self.engine = create_engine(db_uri, echo=False)
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check: get list of students.
    def test_studentList(self):
        r = self.req.get(url('/school/me/students'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        students = data['students']
        self.assertEqual(3, len(students))

        r = self.req.get(url('/school/1/students'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        students = data['students']
        self.assertEqual(3, len(students))

    # Check: create student with bad params.
    def test_newStudentBad(self):
        # Check: not a json
        r = self.req.post(url('/school/me/newstudent'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Not a JSON.', data['description'])

        # Check: empty json
        r = self.req.post(url('/school/me/newstudent'), data='{}', headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        ### Check: missing params

        data = json.dumps({'name': '2'})
        r = self.req.post(url('/school/me/newstudent'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        data = json.dumps({'name': '2', 'login': '22'})
        r = self.req.post(url('/school/me/newstudent'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        data = json.dumps({'name': '2', 'login': '22', 'surname': ''})
        r = self.req.post(url('/school/me/newstudent'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        ### Check: Wrong values

        data = json.dumps({'name': '', 'surname': '', 'login': '', 'passwd': ''})
        r = self.req.post(url('/school/me/newstudent'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

        data = json.dumps({'name': [], 'surname': '', 'login': '', 'passwd': ''})
        r = self.req.post(url('/school/me/newstudent'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

    # Check: create student with correct params
    def test_newStudent(self):
        data = json.dumps({
            'name': 'some',
            'surname': 'sur',
            'login': 'log',
            'passwd': 'pass'
        })
        r = self.req.post(url('/school/me/newstudent'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])
        self.assertEqual(5, data['id'])

    # Check: create duplicate student
    def test_newStudentDuplicate(self):
        student = json.dumps({
            'name': 'some',
            'surname': 'sur',
            'login': 'log',
            'passwd': 'pass'
        })
        r = self.req.post(url('/school/1/newstudent'), data=student, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])
        self.assertEqual(5, data['id'])

        r = self.req.post(url('/school/me/newstudent'), data=student, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Already exists.', data['description'])

    # Check: delete student via bad requests
    def test_delStudentBad(self):
        # Check: malformed request (no action param)
        r = self.req.post(url('/school/1/student/1'), data='{}')
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid action.', data['description'])

        # Check: malformed request (send some post data)
        r = self.req.post(url('/school/1/student/1?action=delete'), data='{}')
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid request.', data['description'])

        # Check: delete non-existent school
        r = self.req.post(url('/school/100/student/1?action=delete'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(403, data['status'])
        self.assertEqual('Forbidden.', data['description'])

        # Check: delete non-existent school with HTTP DELETE
        r = self.req.delete(url('/school/100/student/1'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(403, data['status'])
        self.assertEqual('Forbidden.', data['description'])

        # Check: delete student from another school
        r = self.req.delete(url('/school/me/student/2'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Unknown student.', data['description'])

    # Check: delete student via POST requests
    def test_delStudentPost(self):
        r = self.req.post(url('/school/1/student/1?action=delete'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])

    # Check: delete student via POST requests
    def test_delStudentDelete(self):
        r = self.req.delete(url('/school/1/student/1'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpSchoolTest))
    return suite

if __name__ == '__main__':
    unittest.main()
