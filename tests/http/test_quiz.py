# to use tests_common quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

import requests
import unittest
import json
from sqlalchemy import select
from tests_common import url, db_uri, createAuthFor
#from quiz.core import QuizCore
# self.dbinfo = {'database': db_uri, 'verbose': 'false'}
# self.main = {'admin_password': '', 'guest_allowed_requests': 10}
# self.core = QuizCore(self)


# Quiz get requests (/quiz)
class HttpQuizTest(unittest.TestCase):
    def setUp(self):
        self.req = requests.Session()

        r = self.req.get(url('/authorize'))

        nonce = r.json()['nonce']
        auth = json.dumps(createAuthFor('student', nonce))
        self.headers = {'content-type': 'application/json'}

        r = self.req.post(url('/authorize'), data=auth, headers=self.headers)
        self.assertEqual(200, r.status_code)
        self.assertEqual(200, r.json()['status'])

    # Check: access without authorization
    def test_getNoAuth(self):
        r = requests.get(url('/quiz/1'))
        self.assertEqual(200, r.status_code)
        data = r.json()
        self.assertEqual(401, data['status'])
        self.assertEqual('Unauthorized.', data['description'])

    # Try to get quiz with invalid URL
    def test_getBad(self):
        r = self.req.get(url('/quiz'))
        self.assertEqual(404, r.status_code)

        r = self.req.get(url('/quiz/1/fr'))
        self.assertEqual(404, r.status_code)

        r = self.req.get(url('/quiz/1ds'))
        self.assertEqual(404, r.status_code)

    # Authorize and get quiz list
    # Must return json string with Content-Type: application/json
    def test_get(self):
        r = self.req.get(url('/quiz/1'))
        self.assertEqual(200, r.status_code)
        self.assertEqual('application/json', r.headers['content-type'])

        data = json.loads(r.text)
        self.assertEqual(1, data['topic'])
        self.assertEqual(40, len(data['questions']))

#     # TODO: how to check the language?
#     # Authorize and get quiz list
#     # Must return json string with Content-Type: application/json
#     def test_getLangDe(self):
#         r = self.req.get(url('/quiz/1'), params={'lang': 'de'})
#         self.assertEqual(200, r.status_code)
#         self.assertEqual('application/json', r.headers['content-type'])

#         data = json.loads(r.text)
#         self.assertEqual(1, data['topic'])
#         self.assertEqual(40, len(data['questions']))

#     # TODO: how to check the language?
#     # Authorize and get quiz list
#     # Must return json string with Content-Type: application/json
#     def test_getLangFr(self):
#         r = self.req.get(url('/quiz/1'), params={'lang': 'fr'})
#         self.assertEqual(200, r.status_code)
#         self.assertEqual('application/json', r.headers['content-type'])

#         data = json.loads(r.text)
#         self.assertEqual(1, data['topic'])
#         self.assertEqual(40, len(data['questions']))


# # Quiz post requests (/quiz)
# class QuizPostTest(unittest.TestCase):
#     def setUp(self):
#         self.req = requests.Session()

#         r = self.req.get(url('/authorize'))

#         hdr = r.headers['WWW-Authenticate']
#         auth_txt = createAuthHeader(hdr)
#         headers = {'Authorization': auth_txt}

#         r = self.req.get(url('/authorize'), headers=headers)
#         self.assertEqual(200, r.status_code)

#         self.dbinfo = {'database': db_uri, 'verbose': 'false'}
#         self.db = QuizDb(self)
#         self.stat = self.db.quiz_stat
#         self.conn = self.db.conn
#         self.conn.execute("DELETE from quiz_stat;")

#     def tearDown(self):
#         self.conn.execute("DELETE from quiz_stat;")
#         self.conn.close()

#     # Authorize and send wrong data
#     def test_postBad(self):
#         r = self.req.post(url('/quiz/1'), data={'aa': 12, 'bb': '44'})
#         self.assertEqual(400, r.status_code)
#         self.assertEqual('Missing parameter.', r.text.splitlines()[-1])

#     # # Authorize and send data with the wrong len
#     def test_postBadLen(self):
#         r = self.req.post(url('/quiz/1'), data={'id': [12, 2], 'answer': '44'})
#         self.assertEqual(400, r.status_code)
#         self.assertEqual('Parameters length mismatch.', r.text.splitlines()[-1])

#     # # Authorize and send data with the zero len
#     def test_postBadZeroLen(self):
#         r = self.req.post(url('/quiz/1'), data={'id': [], 'answer': '44'})
#         self.assertEqual(400, r.status_code)
#         self.assertEqual('Missing parameter.', r.text.splitlines()[-1])

#     # # Authorize and send data with the wrong value (only numbers are accepted)
#     def test_postBadVal(self):
#         r = self.req.post(url('/quiz/1'),
#                           data={'id': [12, 'abc'], 'answer': [1, 2]})
#         self.assertEqual(400, r.status_code)
#         self.assertEqual('Invalid value.', r.text.splitlines()[-1])

#     # # Good request
#     def test_postOk(self):
#         r = self.req.post(url('/quiz/1'),
#                           data={'id': [12, '14'], 'answer': [1, 2]})
#         self.assertEqual(200, r.status_code)
#         self.assertEqual('ok', r.text.splitlines()[-1])

#         s = self.stat
#         res = self.conn.execute(select([s]).order_by(s.c.question_id))
#         for row, id in zip(res, [12, 14]):
#             self.assertEqual(1, row[s.c.user_id])
#             self.assertEqual(id, row[s.c.question_id])

#     # Good request wiht string param
#     def test_postOkString(self):
#         r = self.req.post(url('/quiz/1'),
#                           data={'id': "12,14", 'answer': "1,2"})
#         self.assertEqual(200, r.status_code)
#         self.assertEqual('ok', r.text.splitlines()[-1])

#         s = self.stat
#         res = self.conn.execute(select([s]).order_by(s.c.question_id))
#         for row, id in zip(res, [12, 14]):
#             self.assertEqual(1, row[s.c.user_id])
#             self.assertEqual(id, row[s.c.question_id])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpQuizTest))
    # suite.addTest(unittest.makeSuite(QuizPostTest))
    return suite

if __name__ == '__main__':
    unittest.main()
