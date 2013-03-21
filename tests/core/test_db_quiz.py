# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri
from sqlalchemy import select
from quiz.db.quizdb import QuizDb
from quiz.exceptions import QuizCoreError


# Test: generate and save quiz.
# NOTE: question lang and optional fileds are not tested.
class DbQuizTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.db = QuizDb(self)
        self.questions = self.db.questions
        self.answers = self.db.answers
        self.topics_stat = self.db.meta.tables['topics_stat']
        self.engine = self.db.engine
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")

    def tearDown(self):
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")

    # TODO: move to separate test
    def test_getInfo(self):
        info = self.db.getInfo('testuser',
                               'b929d0c46cf5609e0104e50d301b0b8b482e9bfc')
        self.assertEqual('aa4a5443cb91ee1810785314651e5dd1', info['passwd'])
        self.assertEqual(1, info['user_id'])
        self.assertEqual(3, info['app_id'])
        self.assertEqual('student', info['type'])

    # Generate quiz for the user with ID 1 and topic ID 1,
    # questions text must be 'italian', number of questions must be 40.
    def test_get(self):
        quiz = self.db.getQuiz(1, 1, 'it')

        self.assertEqual(40, len(quiz))

        # Pick random question to check it's fields
        # Note: 'image' and 'image_bis' may be absent
        # if values are null for these fields. So we
        # do not check them.
        question = quiz[20]
        self.assertTrue('id' in question)
        self.assertTrue('text' in question)
        self.assertTrue('answer' in question)

        # Get quiz for the topic with with wrong id - must return empty list
        quiz = self.db.getQuiz(9000, 12, 'it')
        self.assertEqual(0, len(quiz))

    # Testing wrong data processing.
    def test_saveBadData(self):
        quiz = self.db.getQuiz(1, 1, 'it')
        questions = [x['id'] for x in quiz]
        questions = list(sorted(questions))

        # Length of questions and answers must be the same
        try:
            self.db.saveQuizResult(1, 1, questions, [0, 0, 0])
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Parameters length mismatch.', err)

        # Questions must contain valid ID values (numbers).
        # We set one of the ID to 'bla' to test this.
        try:
            answers = [0] * len(questions)
            q = questions[:]
            q[3] = 'bla'
            self.db.saveQuizResult(1, 1, q, answers)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid value.', err)

        # Answers must contain 1 or 0.
        # We fill answers with non-numbers.
        try:
            answers = ['bla'] * len(questions)
            self.db.saveQuizResult(1, 1, questions, answers)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid value.', err)

    # Test normal behaviour.
    def test_save(self):
        quiz = self.db.getQuiz(1, 1, 'it')
        questions = [x['id'] for x in quiz]
        questions = list(sorted(questions))

        # Init answers with wrong answers :)
        answers = [0] * len(questions)

        # Put some correct answers
        answers[0:5] = [1] * 5

        self.db.saveQuizResult(1, 1, questions, answers)

        # Check if quiz is saved correctly
        qa = zip(questions, answers)
        s = self.answers
        res = self.engine.execute(select([s]).order_by(s.c.question_id))
        for row, qa in zip(res, qa):
            self.assertEqual(1, row[s.c.user_id])
            self.assertEqual(qa[0], row[s.c.question_id])
            self.assertEqual(qa[1], row[s.c.is_correct])

    # Test unordered question list.
    def test_saveUnordered(self):
        # unordered questions must be saved correctly
        self.db.saveQuizResult(1, 1, [12, 14, 1], [1, 0, 0])

        s = self.answers
        res = self.engine.execute(select([s]).order_by(s.c.question_id))
        rows = res.fetchall()

        self.assertEqual(3, len(rows))
        self.assertEqual(1, rows[0][s.c.user_id])
        self.assertEqual(1, rows[0][s.c.question_id])
        self.assertEqual(1, rows[1][s.c.user_id])
        self.assertEqual(12, rows[1][s.c.question_id])
        self.assertEqual(1, rows[2][s.c.user_id])
        self.assertEqual(14, rows[2][s.c.question_id])

    # Test if answered questions are not present in future quezzes.
    def test_random(self):
        quiz = self.db.getQuiz(1, 1, 'it')
        questions = [x['id'] for x in quiz]
        questions = list(sorted(questions))

        # We set correct answers for questions 2 and 5.
        answers = [0] * len(questions)
        answers[2] = 1
        answers[5] = 1
        q2, q3 = questions[2], questions[5]

        self.db.saveQuizResult(1, 1, questions, answers)

        # Simulate 10 new quzzes and check if
        # answered questions are present in them.
        for x in xrange(10):
            quiz = self.db.getQuiz(1, 1, 'it')
            questions = [x['id'] for x in quiz]
            self.assertTrue(q2 not in questions)
            self.assertTrue(q3 not in questions)

    # If all questions are answered then next quiz will be empty.
    def test_saveall(self):
        quiz = self.db.getQuiz(1, 1, 'it')
        questions = [x['id'] for x in quiz]

        while questions:
            self.db.saveQuizResult(1, 1, questions, [1] * len(questions))
            quiz = self.db.getQuiz(1, 1, 'it')
            questions = [x['id'] for x in quiz]

        quiz = self.db.getQuiz(1, 1, 'it')
        self.assertEqual(0, len(quiz))

    # def test_errorStat(self):
    #     self.db.saveQuizResult(1, 1, [1, 2, 3], [1, 0, 0])

    #     s = self.errors_stat
    #     rows = self.conn.execute(select([s]).order_by(s.c.question_id))
    #     rows = rows.fetchall()
    #     self.assertEqual(2, len(rows))
    #     self.assertEqual(1, rows[0][s.c.user_id])
    #     self.assertEqual(2, rows[0][s.c.question_id])
    #     self.assertEqual(1, rows[1][s.c.user_id])
    #     self.assertEqual(3, rows[1][s.c.question_id])

    #     self.db.saveQuizResult(1, 1, [1, 2, 3], [1, 1, 0])

    #     s = self.errors_stat
    #     rows = self.conn.execute(select([s]).order_by(s.c.question_id))
    #     rows = rows.fetchall()
    #     self.assertEqual(1, len(rows))
    #     self.assertEqual(1, rows[0][s.c.user_id])
    #     self.assertEqual(3, rows[0][s.c.question_id])

    # def test_topicStat(self):
    #     ids = range(1, 11)
    #     answers = [0] * len(ids)
    #     self.db.saveQuizResult(1, 1, ids, answers)

    #     s = self.errors_stat
    #     rows = self.conn.execute(select([s]).order_by(s.c.question_id))
    #     rows = rows.fetchall()
    #     self.assertEqual(10, len(rows))

    #     s = self.topics_stat
    #     rows = self.conn.execute(select([s]))
    #     rows = rows.fetchall()

    #     self.assertEqual(1, len(rows))
    #     self.assertEqual(1, rows[0][s.c.user_id])
    #     self.assertEqual(1, rows[0][s.c.topic_id])
    #     self.assertEqual(5, rows[0][s.c.err_percent])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DbQuizTest))
    return suite

if __name__ == '__main__':
    unittest.main()
