import os.path
import sys
sys.path.append(os.path.join(sys.path[0], '..'))        # to use test_settings

import requests
import unittest
import json
from test_settings import *
from test_auth import get_nonce, create_auth_header, create_digest


# Quiz requests (/quiz)
class QuizTest(unittest.TestCase):
    def setUp(self):
        self.req = requests.Session()

        r = self.req.get(url('/authorize'))
        nonce = get_nonce(r.headers['WWW-Authenticate'])

        digest = create_digest(nonce, 'testuser', 'testpasswd')
        auth_txt = create_auth_header(nonce, app_id, "testuser", digest)
        headers = {'Authorization': auth_txt}

        r = self.req.get(url('/authorize'), headers=headers)
        self.assertEqual(200, r.status_code)

    # Try to get questions without authorization
    def test_getNoAuth(self):
        r = requests.get(url('/quiz'))
        self.assertEqual(401, r.status_code)

    # Try to get quiz with invalid topic
    def test_getBadTopic(self):
        r = self.req.get(url('/quiz'), params={'topic': '1ds'})
        self.assertEqual(400, r.status_code)
        self.assertEqual('Invalid topic value.', r.text.splitlines()[-1])

    # Authorize and get quiz list
    # Must return json string with Content-Type: application/json
    def test_get(self):
        r = self.req.get(url('/quiz'), params={'topic': 1})
        self.assertEqual(200, r.status_code)
        self.assertEqual('application/json', r.headers['content-type'])

        data = json.loads(r.text)
        self.assertEqual(1, data['topic'])
        self.assertEqual(40, len(data['questions']))

    # TODO: how to check the language?
    # Authorize and get quiz list
    # Must return json string with Content-Type: application/json
    def test_getLangDe(self):
        r = self.req.get(url('/quiz'), params={'topic': 1, 'lang': 'de'})
        self.assertEqual(200, r.status_code)
        self.assertEqual('application/json', r.headers['content-type'])

        data = json.loads(r.text)
        self.assertEqual(1, data['topic'])
        self.assertEqual(40, len(data['questions']))

    # TODO: how to check the language?
    # Authorize and get quiz list
    # Must return json string with Content-Type: application/json
    def test_getLangFr(self):
        r = self.req.get(url('/quiz'), params={'topic': 1, 'lang': 'fr'})
        self.assertEqual(200, r.status_code)
        self.assertEqual('application/json', r.headers['content-type'])

        data = json.loads(r.text)
        self.assertEqual(1, data['topic'])
        self.assertEqual(40, len(data['questions']))

    # Authorize and send wrong data
    def test_postBad(self):
        r = self.req.post(url('/quiz'), data={'aa': 12, 'bb': '44'})
        self.assertEqual(400, r.status_code)
        self.assertEqual('Missing parameter.', r.text.splitlines()[-1])

    # # Authorize and send data with the wrong len
    def test_postBadLen(self):
        r = self.req.post(url('/quiz'), data={'id': [12, 2], 'answer': '44'})
        self.assertEqual(400, r.status_code)
        self.assertEqual('Parameters length mismatch.', r.text.splitlines()[-1])

    # # Authorize and send data with the zero len
    def test_postBadZeroLen(self):
        r = self.req.post(url('/quiz'), data={'id': [], 'answer': '44'})
        self.assertEqual(400, r.status_code)
        self.assertEqual('Missing parameter.', r.text.splitlines()[-1])

    # # Authorize and send data with the wrong value (only numbers are accepted)
    def test_postBadVal(self):
        r = self.req.post(url('/quiz'),
            data={'id': [12, 'abc'], 'answer': [1, 2]})
        self.assertEqual(400, r.status_code)
        self.assertEqual('Invalid value.', r.text.splitlines()[-1])

    # # Good request
    def test_postOk(self):
        r = self.req.post(url('/quiz'),
            data={'id': [12, '14'], 'answer': [1, 2]})
        self.assertEqual(200, r.status_code)
        self.assertEqual('ok', r.text.splitlines()[-1])

    # # Good request wiht string param
    def test_postOkString(self):
        r = self.req.post(url('/quiz'), data={'id': "12,14", 'answer': "1,2"})
        self.assertEqual(200, r.status_code)
        self.assertEqual('ok', r.text.splitlines()[-1])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(QuizTest))
    return suite

if __name__ == '__main__':
    unittest.main()
