# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri
from sqlalchemy import select
from quiz.db.quizdb import QuizDb


# TODO: add tests explanations.
class QbQuizTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.db = QuizDb(self)
        self.stat = self.db.quiz_stat
        self.questions = self.db.questions
        self.conn = self.db.conn
        self.conn.execute("DELETE from quiz_stat;")

    def tearDown(self):
        self.conn.execute("DELETE from quiz_stat;")
        self.conn.close()

    def test_getInfo(self):
        info = self.db.getInfo('testuser',
                               'b929d0c46cf5609e0104e50d301b0b8b482e9bfc')
        self.assertEqual('aa4a5443cb91ee1810785314651e5dd1', info['passwd'])
        self.assertEqual(1, info['user_id'])
        self.assertEqual(3, info['app_id'])
        self.assertEqual('student', info['type'])

    def test_getQuiz(self):
        quiz = self.db.getQuiz(1, 1, 'it')
        self.assertEqual(40, len(quiz))
        quiz = self.db.getQuiz(1000, 1, 'it')
        self.assertEqual(0, len(quiz))

    def test_saveQuiz(self):
        # Get some questions
        quiz = self.db.getQuiz(1, 1, 'it')
        ids = [x['id'] for x in quiz][:5]
        answers = [1] * 5
        self.db.saveQuizResult(1, ids, answers)

        # quiz stat must contain only 'ids'
        s = self.stat
        res = self.conn.execute(select([s]).order_by(s.c.question_id))
        for row, id in zip(res, sorted(ids)):
            self.assertEqual(1, row[s.c.user_id])
            self.assertEqual(id, row[s.c.question_id])

    def test_saveQuizUnordered(self):
        ids = [12, 14, 1]
        answers = [1, 0, 0]
        self.db.saveQuizResult(1, ids, answers)

        # quiz stat must contain only '12'
        s = self.stat
        res = self.conn.execute(select([s]).order_by(s.c.question_id))
        rows = res.fetchall()

        self.assertEqual(1, len(rows))
        self.assertEqual(1, rows[0][s.c.user_id])
        self.assertEqual(12, rows[0][s.c.question_id])

    def test_saveQuizAll(self):
        quiz = self.db.getQuiz(1, 1, 'it')
        id_list = []
        while len(quiz):
            ids = [x['id'] for x in quiz]
            id_list.extend(ids)
            answers = [1] * len(ids)
            self.db.saveQuizResult(1, ids, answers)
            quiz = self.db.getQuiz(1, 1, 'it')

        s = self.stat
        res = self.conn.execute(select([s]).order_by(s.c.question_id))
        for row, id in zip(res, sorted(id_list)):
            self.assertEqual(1, row[s.c.user_id])
            self.assertEqual(id, row[s.c.question_id])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(QbQuizTest))
    return suite

if __name__ == '__main__':
    unittest.main()
