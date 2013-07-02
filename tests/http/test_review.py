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


# Test: error review http requests: /errorreview;
# For more info see tests/core/test_review.py
class HttpReviewTest(unittest.TestCase):
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

        self.engine.execute("INSERT IGNORE INTO answers VALUES (3,1,1,0),(3,1,2,0)")

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)
        cleanupdb_onTearDownAccDb(self)

    # Check: get review
    def test_get(self):
        r = self.req.get(url('/errorreview'))
        self.assertEqual(200, r.status_code)

        data = r.json()
        self.assertGreaterEqual(2, len(data['questions']))
        questions = sorted(data['questions'])
        question = questions[0]
        self.assertIn('id', question)
        self.assertIn('text', question)
        self.assertIn('answer', question)
        self.assertEqual(1, questions[0]['id'])
        self.assertEqual(2, questions[1]['id'])

    # Check: get review with lang
    # TODO: how to check the language?
    def test_getLang(self):
        r = self.req.get(url('/errorreview'), params={'lang': 'de'})
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertGreaterEqual(2, len(data['questions']))

        r = self.req.get(url('/errorreview'), params={'lang': 'fr'})
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertGreaterEqual(2, len(data['questions']))

        r = self.req.get(url('/errorreview'), params={'lang': 'it'})
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertGreaterEqual(2, len(data['questions']))

        # if lang is not fr, de or it then it will be used
        r = self.req.get(url('/errorreview'), params={'lang': 'russian'})
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertGreaterEqual(2, len(data['questions']))

    # Check: save with bad values
    def test_saveBad(self):
        # Check: not a json
        r = self.req.post(url('/errorreview'))
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Not a JSON.', data['description'])

        # Check: empty json
        r = self.req.post(url('/errorreview'), data='{}', headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        # Check: missing params
        data = json.dumps({'questions': 0})
        r = self.req.post(url('/errorreview'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        # Check: missing params
        data = json.dumps({'answers': 0})
        r = self.req.post(url('/errorreview'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        ### Check: wrong values params
        ### NOTE: we don't check all errors since core tests does this.

        data = json.dumps({'questions': 0, 'answers': 0})
        r = self.req.post(url('/errorreview'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid value.', data['description'])

        data = json.dumps({'questions': [], 'answers': [1]})
        r = self.req.post(url('/errorreview'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Parameters length mismatch.', data['description'])

        data = json.dumps({'questions': [], 'answers': []})
        r = self.req.post(url('/errorreview'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Empty list.', data['description'])

    # Check: save normal
    def test_save(self):
        data = json.dumps({'questions': [1, 2, 3, 4], 'answers': [1, 1, 1, 0]})
        r = self.req.post(url('/errorreview'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, data['status'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpReviewTest))
    return suite

if __name__ == '__main__':
    unittest.main()
