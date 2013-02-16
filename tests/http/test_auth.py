# to use tests_common
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import unittest
from tests_common import url, createAuthHeader


class AuthTest(unittest.TestCase):
    def setUp(self):
        self.req = requests.Session()

    def test_authHeader(self):
        r = self.req.get(url('/authorize'))
        self.assertEqual(401, r.status_code)

        hdr = r.headers['WWW-Authenticate']
        self.assertEqual('QuizAuth nonce=', hdr[:15])

    def test_authWrongMethod(self):
        headers = {'Authorization': 'hello'}
        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(400, r.status_code)
        self.assertEqual('Invalid parameters.',
                         r.text.splitlines()[-1])

    def test_authWrongParam(self):
        headers = {'Authorization': 'QuizAuth name="2"'}
        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(400, r.status_code)
        self.assertEqual('Invalid parameters.',
                         r.text.splitlines()[-1])

    def test_authWrongAppId(self):
        auth_txt = createAuthHeader('nonce', appkey='12')
        headers = {'Authorization': auth_txt}

        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(400, r.status_code)
        self.assertEqual('Authorization is invalid.',
                         r.text.splitlines()[-1])

    def test_authWrongDigest(self):
        r = self.req.get(url('/authorize'))

        hdr = r.headers['WWW-Authenticate']
        auth_txt = createAuthHeader(hdr, passwd="dd")
        headers = {'Authorization': auth_txt}

        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(400, r.status_code)
        self.assertEqual('Authorization is invalid.',
                         r.text.splitlines()[-1])

    def test_authOk(self):
        r = self.req.get(url('/authorize'))

        hdr = r.headers['WWW-Authenticate']
        auth_txt = createAuthHeader(hdr)
        headers = {'Authorization': auth_txt}

        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(200, r.status_code)
        self.assertTrue('QUIZSID' in r.cookies)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AuthTest))
    return suite

if __name__ == '__main__':
    unittest.main()
