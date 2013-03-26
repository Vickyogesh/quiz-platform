# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from sqlalchemy import select
from tests_common import db_uri
from quiz.core.core import QuizCore


# Test: topic statistics calculation in various situations.
class DbTopicStatTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        self.engine.execute("TRUNCATE TABLE errors;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")
        self.engine.execute("TRUNCATE TABLE quiz_answers;")
        self.engine.execute("TRUNCATE TABLE exam_answers;")
        self.engine.execute("TRUNCATE TABLE exams;")
        self.topic_info = self._getTopicInfo()

    def tearDown(self):
        self.engine.execute("TRUNCATE TABLE errors;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")
        self.engine.execute("TRUNCATE TABLE quiz_answers;")
        self.engine.execute("TRUNCATE TABLE exam_answers;")
        self.engine.execute("TRUNCATE TABLE exams;")

    # Helper function to get number of questions in all topics.
    def _getTopicInfo(self):
        res = self.engine.execute("SELECT id, max_id - min_id + 1 FROM topics")
        return [row[1] for row in res]

    # Check stat if there are no enough info
    def test_empty(self):
        # Try to get stat for invalid user.
        # Even for invalid user it returns statistics (with empty values)
        stat = self.core._getTopicsStat(1000, 'it')
        self.assertEqual(len(self.topic_info), len(stat))

        # Check statistics fields
        for x in stat:
            # -1 means not enough data to calc stat to the topic
            self.assertEqual(-1, x['errors'])
            self.assertTrue('id' in x)
            self.assertTrue('text' in x)

    # Check triggers algo for one topic
    def test_singleTopic(self):
        err = self.core.errors

        # Put one question to the errors table.
        ins = err.insert().values(user_id=1, question_id=1)
        self.engine.execute(ins)

        # We must have one error for the topic.
        # We can skip filtering rules since table is empty initially.
        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(1, res[0])

        # Put more questions.
        ins = err.insert().values([{'user_id': 1, 'question_id': 2},
                                   {'user_id': 1, 'question_id': 3}])
        self.engine.execute(ins)

        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(3, res[0])

        # Remove two questions from the erros table
        d = err.delete().where(err.c.question_id.in_([1, 3]))
        self.engine.execute(d)

        # Now we again have only one error
        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(1, res[0])

        # Remove last error
        d = err.delete().where(err.c.question_id == 2)
        self.engine.execute(d)
        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(0, res[0])

    # Check triggers algo for multiple topics
    def test_multiTopic(self):
        err = self.core.errors

        # Set errors for the topics: 1, 2, 11, 51
        ins = err.insert().values([{'user_id': 1, 'question_id': 2},
                                   {'user_id': 1, 'question_id': 3},
                                   {'user_id': 1, 'question_id': 201},
                                   {'user_id': 1, 'question_id': 205},
                                   {'user_id': 1, 'question_id': 250},
                                   {'user_id': 1, 'question_id': 2001},
                                   {'user_id': 1, 'question_id': 2005},
                                   {'user_id': 1, 'question_id': 10001}
                                   ])
        self.engine.execute(ins)

        res = self.engine.execute("SELECT topic_id, err_count from topics_stat")
        data = [(row[0], row[1]) for row in res]
        self.assertEqual((1, 2), data[0])
        self.assertEqual((2, 3), data[1])
        self.assertEqual((11, 2), data[2])
        self.assertEqual((51, 1), data[3])

    # Check topic stat on exam
    def test_exam(self):
        # If we save exam then topics stat will be updated too.
        # Since exam contains questions from multiple topics then
        # stat for each topic will be updated.

        # Pass exam (set all answers to wrong)
        info = self.core.createExam(1, 'it')
        exam_id = info['exam']['id']
        questions = list(sorted([q['id'] for q in info['questions']]))
        self.core.saveExam(exam_id, questions, [0] * len(questions))

        # Get exam topics
        q = self.core.questions
        sel = select([q.c.topic_id]).where(q.c.id.in_(questions))
        sel = sel.group_by(q.c.topic_id)
        res = self.engine.execute(sel)
        tid = list(sorted([row[0] for row in res]))

        res = self.engine.execute("SELECT topic_id, err_count from topics_stat")
        for row, t in zip(res, tid):
            self.assertEqual(t, row[0])
            # there may be more errors because multiple questions
            # may be picked from one topic for exam.
            self.assertTrue(row[1] >= 1)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DbTopicStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()
