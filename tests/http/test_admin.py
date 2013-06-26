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


# Test: admin http requests: /admin/schools, /admin/newschool
# For more info see tests/core/test_admin.py
class HttpAdminTest(unittest.TestCase):
    def setUp(self):
        self.req = requests.Session()

        r = self.req.get(url('/authorize'))

        nonce = r.json()['nonce']
        auth = json.dumps(createAuthFor('admin', nonce))
        self.headers = {'content-type': 'application/json'}

        r = self.req.post(url('/authorize'), data=auth, headers=self.headers)
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, r.json()['status'])

        self.engine = create_engine(db_uri, echo=False)
        cleanupdb_onSetup(self.engine, drop_users=True)
        cleanupdb_onSetupAccDb(self, drop_users=True)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)
        cleanupdb_onTearDownAccDb(self)

    # Check: get list of schools.
    def test_schoolList(self):
        r = self.req.get(url('/admin/schools'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertIn('schools', data)

    # Check: create school with bad params.
    def test_newSchoolBad(self):
        # Check: not a json
        r = self.req.post(url('/admin/newschool'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Not a JSON.', data['description'])

        # Check: empty json
        r = self.req.post(url('/admin/newschool'), data='{}', headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

        ### Check: missing params

        data = json.dumps({'name': '2'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

        data = json.dumps({'name': '2', 'login': '22'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

        ### Check: Wrong values

        data = json.dumps({'name': '', 'login': '', 'passwd': ''})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

        data = json.dumps({'name': 'dd', 'login': '12', 'passwd': []})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

    # Check: create school with correct params
    def test_newSchool(self):
        data = json.dumps({'name': 'some', 'login': 'log', 'passwd': 'hello'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])
        self.assertEqual(1, data['id'])

    # Check: create duplicate school
    def test_newSchoolDuplicate(self):
        data = json.dumps({'name': 'some', 'login': 'log', 'passwd': 'hello'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])
        self.assertEqual(1, data['id'])

        data = json.dumps({'name': 'some', 'login': 'log', 'passwd': 'hello'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Already exists.', data['description'])

    # Check: delete school via bad requests
    def test_delSchoolBad(self):
        # Check: malformed request (no action param)
        r = self.req.post(url('/admin/school/200'), data='{}', headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid action.', data['description'])

        # Check: malformed request (send some post data)
        r = self.req.post(url('/admin/school/200?action=delete'),
                          data='{}', headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid request.', data['description'])

        # Check: delete non-existent school
        r = self.req.post(url('/admin/school/200?action=delete'),
                          headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Unknown school.', data['description'])

        # Check: delete non-existent school with HTTP DELETE
        r = self.req.delete(url('/admin/school/200'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(400, data['status'])
        self.assertEqual('Unknown school.', data['description'])

    # Check: delete school via POST request
    def test_delSchoolPost(self):
        # Create one school
        data = json.dumps({'name': 'some', 'login': 'log', 'passwd': 'hello'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])
        self.assertEqual(1, data['id'])

        r = self.req.post(url('/admin/school/1?action=delete'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])

    # Check: delete school via DELETE request
    def test_delSchoolDelete(self):
        return
        # Create one school
        data = json.dumps({'name': 'some', 'login': 'log', 'passwd': 'hello'})
        r = self.req.post(url('/admin/newschool'), data=data, headers=self.headers)
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])
        self.assertEqual(1, data['id'])

        # Check: delete non-existent school with HTTP DELETE
        r = self.req.delete(url('/admin/school/1'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(200, data['status'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpAdminTest))
    return suite

if __name__ == '__main__':
    unittest.main()
