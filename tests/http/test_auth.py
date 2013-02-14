import os.path
import sys
sys.path.append(os.path.join(sys.path[0], '..'))        # to use test_settings

import requests
import unittest
import hashlib
from test_settings import *


def get_nonce(header):
    return header[16:-1]


def create_auth_header(nonce, app_id, username, digest):
    fmt = 'QuizAuth nonce="{0}", appid="{1}", username="{2}", digest="{3}"'
    return fmt.format(nonce, app_id, username, digest)


def create_digest(nonce, username, passwd):
    m = hashlib.md5()
    m.update('%s:%s' % (username, passwd))
    ha1 = m.hexdigest()
    m = hashlib.md5()
    m.update('%s:%s' % (nonce, ha1))
    return m.hexdigest()


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
        auth_txt = create_auth_header('nonce', "12", "testuser", "dd")
        headers = {'Authorization': auth_txt}

        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(400, r.status_code)
        self.assertEqual('Authorization is invalid.',
                         r.text.splitlines()[-1])

    def test_authWrongDigest(self):
        r = self.req.get(url('/authorize'))
        nonce = get_nonce(r.headers['WWW-Authenticate'])

        auth_txt = create_auth_header(nonce, app_id, "testuser", "dd")
        headers = {'Authorization': auth_txt}

        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(400, r.status_code)
        self.assertEqual('Authorization is invalid.',
                         r.text.splitlines()[-1])

    def test_authOk(self):
        r = self.req.get(url('/authorize'))
        nonce = get_nonce(r.headers['WWW-Authenticate'])

        digest = create_digest(nonce, 'testuser', 'testpasswd')
        auth_txt = create_auth_header(nonce, app_id, "testuser", digest)
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
