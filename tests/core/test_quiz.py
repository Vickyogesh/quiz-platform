# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from sqlalchemy import select
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: generate and save quiz.
# NOTE: question lang and optional fileds are not tested.
class CoreQuizTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.quiz_answers = self.core.quiz_answers
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # TODO: move to separate test
    def test_getInfo(self):
        name = 'testuser'
        appkey = 'b929d0c46cf5609e0104e50d301b0b8b482e9bfc'

        appid = self.core.getAppId(appkey)
        user = self.core.getUserInfo(name, with_passwd=True)

        self.assertEqual('aa4a5443cb91ee1810785314651e5dd1', user['passwd'])
        self.assertEqual(3, user['id'])
        self.assertEqual(3, appid)
        self.assertEqual('student', user['type'])

    # Generate quiz for the user with ID 1 and topic ID 1,
    # questions text must be 'italian', number of questions must be 40.
    def test_get(self):
        quiz = self.core.getQuiz(3, 1, 'it')
        questions = quiz['questions']

        self.assertEqual(1, quiz['topic'])
        self.assertEqual(40, len(questions))

        # Pick random question to check it's fields
        # Note: 'image' and 'image_bis' may be absent
        # if values are null for these fields. So we
        # do not check them.
        question = questions[20]
        self.assertTrue('id' in question)
        self.assertTrue('text' in question)
        self.assertTrue('answer' in question)

        # Get quiz for the topic with with wrong id - must return empty list
        quiz = self.core.getQuiz(12, 9000, 'it')
        self.assertEqual(0, len(quiz['questions']))

    # Testing wrong data processing.
    def test_saveBadData(self):
        quiz = self.core.getQuiz(3, 1, 'it')
        quiz = quiz['questions']
        questions = [x['id'] for x in quiz]
        questions = list(sorted(questions))

        # Length of questions and answers must be the same
        try:
            self.core.saveQuiz(3, 1, questions, [0, 0, 0])
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Parameters length mismatch.', err)
        err = ''

        # Try to save empty lists
        try:
            self.core.saveQuiz(3, 1, [], [])
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Empty list.', err)
        err = ''

        # Questions must contain valid ID values (numbers).
        # We set one of the ID to 'bla' to test this.
        try:
            answers = [0] * len(questions)
            q = questions[:]
            q[3] = 'bla'
            self.core.saveQuiz(3, 1, q, answers)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid value.', err)
        err = ''

        # Answers must contain 1 or 0.
        # We fill answers with non-numbers.
        try:
            answers = ['bla'] * len(questions)
            self.core.saveQuiz(3, 1, questions, answers)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid value.', err)

    # Test normal behaviour.
    def test_save(self):
        quiz = self.core.getQuiz(3, 1, 'it')
        quiz = quiz['questions']
        questions = [x['id'] for x in quiz]
        questions = list(sorted(questions))

        # Init answers with wrong answers :)
        answers = [0] * len(questions)

        # Put some correct answers
        answers[0:5] = [1] * 5

        self.core.saveQuiz(3, 1, questions, answers)

        # Check if quiz is saved correctly
        qa = zip(questions, answers)
        s = self.quiz_answers
        res = self.engine.execute(select([s]).order_by(s.c.question_id))
        for row, qa in zip(res, qa):
            self.assertEqual(3, row[s.c.user_id])
            self.assertEqual(qa[0], row[s.c.question_id])
            self.assertEqual(qa[1], row[s.c.is_correct])

    # Test unordered question list.
    def test_saveUnordered(self):
        # unordered questions must be saved correctly
        self.core.saveQuiz(3, 1, [12, 14, 1], [1, 0, 0])

        s = self.quiz_answers
        res = self.engine.execute(select([s]).order_by(s.c.question_id))
        rows = res.fetchall()

        self.assertEqual(3, len(rows))
        self.assertEqual(3, rows[0][s.c.user_id])
        self.assertEqual(1, rows[0][s.c.question_id])
        self.assertEqual(3, rows[1][s.c.user_id])
        self.assertEqual(12, rows[1][s.c.question_id])
        self.assertEqual(3, rows[2][s.c.user_id])
        self.assertEqual(14, rows[2][s.c.question_id])

    # Test if answered questions are not present in future quezzes.
    def test_random(self):
        quiz = self.core.getQuiz(3, 1, 'it')
        quiz = quiz['questions']
        questions = [x['id'] for x in quiz]
        questions = list(sorted(questions))

        # We set one correct and one wrong answer
        # for questions 2 and 5.
        answers = [0] * len(questions)
        answers[2] = 1
        answers[5] = 0
        q2, q3 = questions[2], questions[5]

        self.core.saveQuiz(3, 1, questions, answers)

        # Simulate 10 new quzzes and check if
        # answered questions are present in them.
        for x in xrange(10):
            quiz = self.core.getQuiz(3, 1, 'it')
            quiz = quiz['questions']
            questions = [x['id'] for x in quiz]
            self.assertTrue(q2 not in questions)
            self.assertTrue(q3 not in questions)

    # If all questions are answered then next quiz will be empty.
    # Not true: quiz always return questions.
    # def test_saveall(self):
    #     quiz = self.core.getQuiz(1, 1, 'it')
    #     quiz = quiz['questions']
    #     questions = [x['id'] for x in quiz]

    #     while questions:
    #         self.core.saveQuiz(1, 1, questions, [1] * len(questions))
    #         quiz = self.core.getQuiz(1, 1, 'it')
    #         quiz = quiz['questions']
    #         questions = [x['id'] for x in quiz]

    #     quiz = self.core.getQuiz(1, 1, 'it')
    #     self.assertEqual(0, len(quiz['questions']))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreQuizTest))
    return suite

if __name__ == '__main__':
    unittest.main()
