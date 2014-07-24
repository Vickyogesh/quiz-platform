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


# Test: Exam http requests: /exam, /exam/<id>;
# For more info see tests/core/test_exam.py
class HttpExamTest(unittest.TestCase):
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

    # Check: get exam
    def test_get(self):
        r = self.req.get(url('/exam'))
        self.assertEqual(200, r.status_code)

        data = r.json()
        exam = data['exam']
        self.assertIn('id', exam)
        self.assertIn('expires', exam)
        self.assertEqual(40, len(data['questions']))

        question = data['questions'][0]
        self.assertIn('id', question)
        self.assertIn('text', question)
        self.assertIn('answer', question)

    # Check: get exam with lang
    # TODO: how to check the language?
    def test_getLang(self):
        for lang in ['fr', 'de', 'it']:
            r = self.req.get(url('/exam'), params={'lang': lang})
            self.assertEqual(200, r.status_code)
            data = r.json()

            exam = data['exam']
            self.assertIn('id', exam)
            self.assertIn('expires', exam)
            self.assertEqual(40, len(data['questions']))

            question = data['questions'][0]
            self.assertIn('id', question)
            self.assertIn('text', question)
            self.assertIn('answer', question)

    # Check: get exam info
    def test_getInfo(self):
        r = self.req.get(url('/exam'))
        exam_id = r.json()['exam']['id']
        r = self.req.get(url('/exam/' + str(exam_id)))

        data = r.json()
        self.assertIn('student', data)
        self.assertIn('exam', data)
        self.assertIn('questions', data)

    # Check: get exam info with lang
    def test_getInfoLang(self):
        r = self.req.get(url('/exam'))
        exam_id = r.json()['exam']['id']
        for lang in ['fr', 'de', 'it', 'ru']:
            r = self.req.get(url('/exam/' + str(exam_id)), params={'lang': lang})
            data = r.json()
            self.assertIn('student', data)
            self.assertIn('exam', data)
            self.assertIn('questions', data)

    # Check: save exam with bad data
    def test_saveBad(self):
        r = self.req.get(url('/exam'))
        eid = r.json()['exam']['id']

        # Check: not a json
        r = self.req.post(url('/exam/%d' % eid))
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Not a JSON.', data['description'])

        # Check: empty json
        r = self.req.post(url('/exam/%d' % eid), data='{}', headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        # Check: missing params
        data = json.dumps({'questions': 0})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        # Check: missing params
        data = json.dumps({'answers': 0})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Missing parameter.', data['description'])

        ### Check: wrong values params
        ### NOTE: we don't check all errors since core tests does this.

        data = json.dumps({'questions': 0, 'answers': 0})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid value.', data['description'])

        data = json.dumps({'questions': [], 'answers': [1]*40})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Parameters length mismatch.', data['description'])

        data = json.dumps({'questions': [], 'answers': []})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Wrong number of answers.', data['description'])

        # Check: save non existent exam
        data = json.dumps({'questions': [1]*40, 'answers': [1]*40})
        r = self.req.post(url('/exam/100'), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid exam ID.', data['description'])

        # Check: wrong questions ID
        data = json.dumps({'questions': [1]*40, 'answers': [1]*40})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(400, r.status_code)
        self.assertEqual(400, data['status'])
        self.assertEqual('Invalid question ID.', data['description'])

    # Check: normal save
    def test_save(self):
        r = self.req.get(url('/exam'))
        data = r.json()
        eid = data['exam']['id']
        questions = [x['id'] for x in data['questions']]
        data = json.dumps({'questions': questions, 'answers': [1]*40})
        r = self.req.post(url('/exam/%d' % eid), data=data, headers=self.headers)
        data = r.json()
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, data['status'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpExamTest))
    return suite

if __name__ == '__main__':
    unittest.main()
