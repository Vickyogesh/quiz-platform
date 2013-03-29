# to use tests_common
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import unittest
import json
from tests_common import url, createAuthData, createAuthFor


# Test: authorization http requests: /authorize;
class HttpAuthTest(unittest.TestCase):
    def setUp(self):
        self.req = requests.Session()
        self.headers = {'content-type': 'application/json'}

    def test_getAuth(self):
        r = requests.get(url('/authorize'))
        self.assertEqual(200, r.status_code)

        data = r.json()
        self.assertTrue('nonce' in data)
        self.assertEqual(401, data['status'])

    def test_sendMalformed(self):
        # Send non JSON.
        r = requests.post(url('/authorize'), data='')
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Not a JSON.', data['description'])

        # Send non JSON.
        r = requests.post(url('/authorize'), headers=self.headers, data='')
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Not a JSON.', data['description'])

        # Send empty JSON.
        r = requests.post(url('/authorize'), headers=self.headers, data='{}')
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

        # Send with missing params.
        data = json.dumps({'nonce': 12, 'login': 'hi', 'appid': 'ff'})
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid parameters.', data['description'])

    # NOTE: currently the service doesn't save generated nonce,
    # so client may generate it by itself - this is a security issue
    # and must be improved to increase security.
    # Thus we can't check malformed nonce.
    def test_sendWrong(self):
        # Wrong login
        data = json.dumps(createAuthData(12, login=[1, 2]))
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Authorization is invalid.', data['description'])

        # Wrong login
        data = json.dumps(createAuthData(12, appkey=[1, 2]))
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Authorization is invalid.', data['description'])

        # Wrong digest
        data = createAuthData(12)
        data['digest'] = [1, 2]
        data = json.dumps(data)
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Authorization is invalid.', data['description'])

    # See previuos note
    def test_ok(self):
        data = json.dumps(createAuthFor('student'))
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, data['status'])
        self.assertIn('sid', data)
        self.assertIn('QUIZSID', r.cookies)

        user = data['user']
        self.assertEqual('Test', user['name'])
        self.assertEqual('User', user['surname'])
        self.assertEqual('student', user['type'])
        self.assertIn('id', user)

    ### Check various types of users

    def test_authAdmin(self):
        data = json.dumps(createAuthFor('admin'))
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        user = r.json()['user']
        self.assertEqual('admin', user['name'])
        self.assertEqual('admin', user['type'])
        self.assertEqual(0, user['id'])
        self.assertNotIn('surname', user)

    def test_authSchool(self):
        data = json.dumps(createAuthFor('school'))
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        user = r.json()['user']
        self.assertEqual('Chuck Norris School', user['name'])
        self.assertEqual('school', user['type'])
        self.assertIn('id', user)
        self.assertNotIn('surname', user)

    def test_authGuest(self):
        data = json.dumps(createAuthFor('guest'))
        r = requests.post(url('/authorize'), headers=self.headers, data=data)
        user = r.json()['user']
        self.assertEqual('Chuck Norris School', user['name'])
        self.assertEqual('', user['surname'])
        self.assertEqual('guest', user['type'])
        self.assertIn('id', user)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpAuthTest))
    return suite

if __name__ == '__main__':
    unittest.main()
