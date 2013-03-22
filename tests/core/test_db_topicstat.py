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
        self.core = QuizCore(self)
        self.answers = self.core.answers
        self.topics_stat = self.core.meta.tables['topics_stat']
        self.engine = self.core.engine
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")
        self.engine.execute("TRUNCATE TABLE exams_stat;")
        self.engine.execute("TRUNCATE TABLE exams;")
        self.topic_info = self._getTopicInfo()

    def tearDown(self):
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")
        self.engine.execute("TRUNCATE TABLE exams_stat;")
        self.engine.execute("TRUNCATE TABLE exams;")

    # Helper function to get number of questions in all topics.
    def _getTopicInfo(self):
        res = self.engine.execute("SELECT id, max_id - min_id + 1 FROM topics")
        return [row[1] for row in res]

    # Check stat if there are no answers
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

    # Check stat algo for topics with empty answers
    def test_fresh(self):
        ans = self.answers

        # We put one correct answer.
        # In this situation nothing happens since we don't update
        # existing answer and trigger linked to answers will not update
        # topics_stat.err_count.
        # See _createFuncs() in misc/dbtools.py for more info about
        # triggers logic.
        ins = ans.insert().values(user_id=1, question_id=1, is_correct=1)
        self.engine.execute(ins)

        # we can skip filtering rules since table is empty initially.
        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()

        # result is zero because answers table trigger adds row
        # with err_count=0 for the topic because answer is correct.
        self.assertFalse(res[0])

        # now we insert wrong answer for the topic 2
        qid = self.topic_info[0] + 1  # first question for the topic 2
        ins = ans.insert().values(user_id=1, question_id=qid, is_correct=0)
        self.engine.execute(ins)

        # Now we have two rows:
        #   topic1 err_cout=0
        #   topic2 err_cout=1
        # Second row is added by the trigger on new wrong answer
        res = self.engine.execute("SELECT topic_id, err_count from topics_stat")
        data = [(row[0], row[1]) for row in res]

        self.assertEqual((1, 0), data[0])
        self.assertEqual((2, 1), data[1])

    # Check errors number update
    def test_update(self):
        # Let's create a bunch of correct answers
        answers = [{'user_id': 1, 'question_id': x, 'is_correct': 1}
                   for x in xrange(1, 10)]

        ins = self.answers.insert().values(answers)
        self.engine.execute(ins)

        # At this point we have one row in the topics_stat
        # for the topic 1 with err_count=0.
        # Now we set some answers as wrong.
        ans = self.answers
        upd = ans.update()
        upd = upd.where(ans.c.question_id.in_([1, 2, 3])).values(is_correct=0)
        self.engine.execute(upd)

        # Errors count for the topic 1 must be updated.
        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(3, res[0])

        # Now set some wrong answers to correct again
        upd = ans.update()
        upd = upd.where(ans.c.question_id.in_([2, 3])).values(is_correct=1)
        self.engine.execute(upd)

        # And err_count have to decrease.
        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(1, res[0])

        # if we insert more correct answers then err_count will be unchanged.
        ins = self.answers.insert().values(user_id=1, question_id=20, is_correct=1)
        self.engine.execute(ins)

        res = self.engine.execute("SELECT err_count from topics_stat").fetchone()
        self.assertEqual(1, res[0])

        # Let's check topic id
        res = self.engine.execute("SELECT topic_id from topics_stat").fetchone()
        self.assertEqual(1, res[0])

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
