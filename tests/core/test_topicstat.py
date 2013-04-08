# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from collections import namedtuple
from datetime import datetime, timedelta
from sqlalchemy import select
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore

TopicErrLastRow = namedtuple('TopicErrLastRow', 'user topic date err count, week month')
TopicErrSnapshotRow = namedtuple('TopicErrSnapshotRow', 'user topic date err')
R = TopicErrLastRow
S = TopicErrSnapshotRow


def now():
    return datetime.utcnow().date()


# Test: topic_err_current and topic_err_history
class CoreTopicHistoryTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check: add new answer.
    # answers -> topic_err_current -> topic_err_snapshot
    # If you add answer then new row must be created in the
    # topic_err_current (if it present then it must be updated).
    # Also new row will be added to the topic_err_snapshot
    # (or updated if date the same).
    def test_add(self):
        self.engine.execute("INSERT INTO answers VALUES(4, 1, 0)")
        res = self.engine.execute("SELECT * FROM topic_err_current").fetchall()
        self.assertEqual(1, len(res))
        self.assertEqual(R(user=4, topic=1, date=now(),
                           err=1, count=1, week=-1, month=-1), res[0])

        self.engine.execute("INSERT INTO answers VALUES(4, 2, 1)")
        res = self.engine.execute("SELECT * FROM topic_err_current").fetchall()
        self.assertEqual(1, len(res))
        self.assertEqual(R(user=4, topic=1, date=now(),
                           err=1, count=2, week=-1, month=-1), res[0])

        self.engine.execute("INSERT INTO answers VALUES(4, 203, 1)")
        res = self.engine.execute("SELECT * FROM topic_err_current").fetchall()
        self.assertEqual(2, len(res))
        self.assertEqual(R(user=4, topic=1, date=now(), err=1,
                           count=2, week=-1, month=-1), res[0])
        self.assertEqual(R(user=4, topic=2, date=now(), err=0,
                           count=1, week=-1, month=-1), res[1])

        res = self.engine.execute("SELECT * FROM topic_err_snapshot").fetchall()
        self.assertEqual(2, len(res))
        self.assertEqual(S(user=4, topic=1, date=now(), err=50), res[0])
        self.assertEqual(S(user=4, topic=2, date=now(), err=0), res[1])

    # Check: update existent answer
    def test_update(self):
        R = TopicErrLastRow

        self.engine.execute("INSERT INTO answers VALUES (4, 1, 0), (4, 2, 1)")
        self.engine.execute("UPDATE answers SET is_correct=1 WHERE question_id=1")
        res = self.engine.execute("SELECT * FROM topic_err_current").fetchall()
        self.assertEqual(1, len(res))
        self.assertEqual(R(user=4, topic=1, date=now(), err=0,
                           count=2, week=-1, month=-1), res[0])
        res = self.engine.execute("SELECT * FROM topic_err_snapshot").fetchall()
        self.assertEqual(1, len(res))
        self.assertEqual(S(user=4, topic=1, date=now(), err=0), res[0])

    def test_snapshot(self):
        curr = self.core.meta.tables['topic_err_current']
        t = self.core.meta.tables['topic_err_snapshot']
        dt = now()

        # add 60 snapshots (~2 month data)
        lst = []
        for x in xrange(60):
            lst.append({
                'user_id': 4,
                'topic_id': 1,
                'now_date': dt - timedelta(days=x),
                'err_percent': 12 + x
            })
        self.engine.execute(t.insert(), lst)
        # res = self.engine.execute(t.select()).fetchall()
        # for r in res:
        #     print r

        tm = dt - timedelta(days=4)
        self.engine.execute(curr.insert(), user_id=4, topic_id=1, now_date=tm,
                            err_count=20, count=40)
        #res = self.engine.execute("SELECT * FROM topic_err_current").fetchone()


# Test: topic statistics calculation in various situations.
@unittest.skip
class CoreTopicStatTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)
        self.topic_info = self._getTopicInfo()

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

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
            self.assertIn('id', x)
            self.assertIn('text', x)

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
    suite.addTest(unittest.makeSuite(CoreTopicHistoryTest))
    #suite.addTest(unittest.makeSuite(CoreTopicStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()
