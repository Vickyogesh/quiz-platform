# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri
from quiz.db.quizdb import QuizDb


# TODO: add tests explanations.
class DbStatTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.db = QuizDb(self)
        self.questions = self.db.questions
        self.answers = self.db.answers
        self.topics_stat = self.db.meta.tables['topics_stat']
        self.engine = self.db.engine
        self.engine.execute("DELETE from answers;")
        self.engine.execute("DELETE from topics_stat;")

    def tearDown(self):
        self.engine.execute("DELETE from answers;")
        self.engine.execute("DELETE from topics_stat;")

    # Save one question with wrong answer.
    # There must be 1 error for the topic 1, since we have one wrong answer.
    def test_quizTopicsStat1(self):
        questions = [1]
        answers = [0]
        self.db.saveQuizResult(1, 1, questions, answers)

        rows = self.engine.execute("SELECT * FROM topics_stat;")
        rows = rows.fetchall()
        self.assertEqual(1, len(rows))
        row = rows[0]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(1, row[1])  # topic_id
        self.assertEqual(1, row[2])  # err percent

    def test_quizTopicsStat2(self):
        # Before testing we get topics data: questions ID ranges for each topic
        ranges = {}
        rows = self.engine.execute("""SELECT id, max_id, min_id FROM topics
            WHERE id IN (1, 3, 5);
        """)
        rows = rows.fetchall()
        for row in rows:
            ranges[row[0]] = {'max': row[1], 'min': row[2]}

        # Now we can generate questions & answers for each topic.
        # We generate 20 errors for each topic.
        questions = []
        answers = []
        for topic in ranges:
            info = ranges[topic]
            questions += [info['min'] + m for m in xrange(20)]
        answers = [0] * len(questions)
        self.db.saveQuizResult(1, 1, questions, answers)

        rows = self.engine.execute("SELECT * FROM topics_stat;")
        rows = rows.fetchall()
        self.assertEqual(3, len(rows))

        row = rows[0]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(1, row[1])  # topic_id
        self.assertEqual(20, row[2])  # err percent

        row = rows[1]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(3, row[1])  # topic_id
        self.assertEqual(20, row[2])  # err percent

        row = rows[2]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(5, row[1])  # topic_id
        self.assertEqual(20, row[2])  # err percent

        # Now we update statistics by set correct answers for 9 questions
        # in each topic, thus number of errors must be 11 for each topic
        questions = []
        answers = []
        for topic in ranges:
            info = ranges[topic]
            questions += [info['min'] + m for m in xrange(9)]
        answers = [1] * len(questions)
        self.db.saveQuizResult(1, 1, questions, answers)

        rows = self.engine.execute("SELECT * FROM topics_stat;")
        rows = rows.fetchall()
        self.assertEqual(3, len(rows))

        row = rows[0]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(1, row[1])  # topic_id
        self.assertEqual(11, row[2])  # err percent

        row = rows[1]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(3, row[1])  # topic_id
        self.assertEqual(11, row[2])  # err percent

        row = rows[2]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(5, row[1])  # topic_id
        self.assertEqual(11, row[2])  # err percent

    # If we put only correct answers then topics stat must
    # contain zero erros number.
    def test_quizTopicsStat3(self):
        # Here we get min question ID for the topic 4
        # and generate 20 questions and correct answers.
        rows = self.engine.execute("SELECT min_id FROM topics WHERE id=4")
        min_id = rows.fetchall()[0][0]
        questions = [min_id + m for m in xrange(20)]
        answers = [1] * len(questions)

        # After saving questions we must have statistics only
        # for the topic 4 and errors count must be zero
        # since we saved only correct answers.
        self.db.saveQuizResult(1, 1, questions, answers)
        rows = self.engine.execute("SELECT * FROM topics_stat;")
        rows = rows.fetchall()
        self.assertEqual(1, len(rows))

        row = rows[0]
        self.assertEqual(1, row[0])  # user_id
        self.assertEqual(4, row[1])  # topic_id
        self.assertEqual(0, row[2])  # err percent


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DbStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()
