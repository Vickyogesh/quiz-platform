# to use tests_common and quiz module
import os.path
import sys
from datetime import datetime as dt
from datetime import timedelta

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

import unittest
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from sqlalchemy import and_


# TODO: test drop users trigger.
# TODO: test school's students rating.
# Test: DB stored procedures and triggers;
# they are created in the misc/dbtools/func.py
class CoreDbTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine, True)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    def sql(self, *args, **kwargs):
        return self.engine.execute(*args, **kwargs)

    # Test: user add trigger.
    # from misc/dbtools/func.py users():
    # If guest is added then we update guest access info.
    # If new student is added then create snapshot entry.
    def test_users_add(self):
        # Check: add guest
        self.sql("""INSERT INTO users(id, type, quiz_type, school_id)
                     VALUES(1, 'guest', 2, 1)""")

        # Now we have entry in the guest_access
        row = self.sql("SELECT * FROM guest_access WHERE id=1")
        row = row.fetchall()
        self.assertEqual(1, len(row))

        row = row[0]
        self.assertEqual(1, row[0])  # id
        self.assertEqual(2, row[1])  # quiz_type
        self.assertEqual(0, row[2])  # num_requests
        # check period_end
        tm = dt.utcnow() + timedelta(hours=1)
        delta = tm - row[3]
        self.assertLess(delta, timedelta(seconds=10))

        # Check: no entry in the user_progress_snapshot
        row = self.sql("SELECT * FROM user_progress_snapshot WHERE user_id=1")
        row = row.fetchall()
        self.assertEqual(0, len(row))

        # Check: add student
        # There must be no entry in the user_progress_snapshot.
        self.sql("""INSERT INTO users(id, type, quiz_type, school_id)
                     VALUES(2, 'student', 2, 1)""")
        row = self.sql("SELECT * FROM user_progress_snapshot WHERE user_id=2")
        row = row.fetchall()
        self.assertEqual(0, len(row))

    # NOTE: users.progress_coef is not used anymore
    # and user_progress_snapshot.progress_coef is updated by the
    # on_exams_after_upd trigger dirrectly not by users table triggers.
    # See exams() in the dbtools/func.py.
    # Old behaviour:
    #   If progress_coef is changed for the student
    #   then update snapshot entry.
    # New behaviour: nothing happens.
    # Test: user update trigger.
    @unittest.skip('users.progress_coef is not used anymore')
    def test_users_update(self):
        # Add guest and stundet.
        self.sql("""INSERT INTO users(id, type, quiz_type, school_id)
                     VALUES(1, 'guest', 2, 1)""")
        self.sql("""INSERT INTO users(id, type, quiz_type, school_id)
                     VALUES(2, 'student', 2, 1)""")

        s = self.sql("SELECT * FROM user_progress_snapshot WHERE user_id=2")
        print s.fetchall()

        # If progress_coef is changed for the student
        # then update snapshot entry.
        self.sql("UPDATE users SET progress_coef=12 WHERE id=2")
        row = self.sql("""SELECT progress_coef FROM user_progress_snapshot
                       WHERE user_id=2""").fetchone()
        self.assertEqual(12, row[0])

        # If user activity timestamp is changed and if user is guest
        # then we update number of requests.
        u = self.core.users
        last = dt.utcnow()
        sql = u.update().values(last_visit=last)
        sql = sql.where(u.c.id == 1)
        self.sql(sql)

        row = self.sql("""SELECT num_requests FROM guest_access
                       WHERE id=1""").fetchone()
        self.assertEqual(1, row[0])

        # Also last school activity is updated in the school_stat_cache.
        row = self.sql("""SELECT last_activity FROM school_stat_cache
                       WHERE school_id=1 AND quiz_type=2""").fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertLessEqual(last - row[0], timedelta(seconds=2))

    # Test: update/insert quiz answers.
    def test_quiz_answers(self):
        a = self.core.answers
        q = self.core.quiz_answers

        # After inserting quiz answer we update answers table.
        sql = q.insert().values(user_id=1, quiz_type=2,
                                question_id=1, is_correct=0)
        self.sql(sql)

        sql = q.insert().values(user_id=1, quiz_type=2,
                                question_id=100, is_correct=1)
        self.sql(sql)

        row = self.sql(a.select()).fetchall()
        self.assertEqual(2, len(row))

        self.assertEqual(1, row[0][a.c.user_id])
        self.assertEqual(2, row[0][a.c.quiz_type])
        self.assertEqual(1, row[0][a.c.question_id])
        self.assertEqual(0, row[0][a.c.is_correct])

        self.assertEqual(1, row[1][a.c.user_id])
        self.assertEqual(2, row[1][a.c.quiz_type])
        self.assertEqual(100, row[1][a.c.question_id])
        self.assertEqual(1, row[1][a.c.is_correct])

        # After updating quiz answer we update answers table.
        sql = q.update().values(is_correct=0).where(q.c.question_id == 100)
        self.sql(sql)

        row = self.sql(a.select()).fetchall()
        self.assertEqual(2, len(row))

        self.assertEqual(1, row[0][a.c.user_id])
        self.assertEqual(2, row[0][a.c.quiz_type])
        self.assertEqual(1, row[0][a.c.question_id])
        self.assertEqual(0, row[0][a.c.is_correct])

        self.assertEqual(1, row[1][a.c.user_id])
        self.assertEqual(2, row[1][a.c.quiz_type])
        self.assertEqual(100, row[1][a.c.question_id])
        self.assertEqual(0, row[1][a.c.is_correct])

    # Test: update exam answer.
    # Before updating exam answer we update answer table.
    def test_exam_answers(self):
        e = self.core.exams
        exa = self.core.exam_answers
        a = self.core.answers

        # Create fake exam to link user id to exam
        sql = e.insert().values(quiz_type=2, user_id=2, start_time=dt.utcnow())
        self.sql(sql)

        # Now we insert one exam answer.
        # In real life (see createExam() in quiz/core/exammixin.py)
        # after ceating exam we also insert exam questions to the
        # exam_answers and later update them with real answers.
        # So here we emulate two answers update.
        sql = exa.insert().values([
            {'question_id': 1, 'quiz_type': 2, 'exam_id': 1},
            {'question_id': 2, 'quiz_type': 2, 'exam_id': 1}
        ])
        self.sql(sql)

        # Check: no answers added to the answers table at this moment.
        res = self.sql(a.select()).fetchall()
        self.assertFalse(res)

        # Let's update answer for question with ID 1:
        sql = exa.update().values(is_correct=True).where(and_(
            exa.c.question_id == 1, exa.c.quiz_type == 2))
        self.sql(sql)

        # There must be one entry in the answers
        row = self.sql(a.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(2, row[a.c.user_id])
        self.assertEqual(2, row[a.c.quiz_type])
        self.assertEqual(1, row[a.c.question_id])
        self.assertEqual(1, row[a.c.is_correct])

        # Let's update answer for question with ID 2:
        sql = exa.update().values(is_correct=False).where(and_(
            exa.c.question_id == 2, exa.c.quiz_type == 2))
        self.sql(sql)

        # There must be two entries in the answers
        row = self.sql(a.select()).fetchall()
        self.assertEqual(2, len(row))

        # answer 1
        self.assertEqual(2, row[0][a.c.user_id])
        self.assertEqual(2, row[0][a.c.quiz_type])
        self.assertEqual(1, row[0][a.c.question_id])
        self.assertEqual(1, row[0][a.c.is_correct])
        # answer 2
        self.assertEqual(2, row[1][a.c.user_id])
        self.assertEqual(2, row[1][a.c.quiz_type])
        self.assertEqual(2, row[1][a.c.question_id])
        self.assertEqual(0, row[1][a.c.is_correct])

    # Test: delete exam.
    # Before delete exam we delete exam's answers.
    def test_exams_del(self):
        e = self.core.exams
        ea = self.core.exam_answers

        # Create exam with 2 answers.
        # And also we insert answer for another exam
        self.sql(e.insert().values(quiz_type=2, user_id=2,
                                   start_time=dt.utcnow()))
        self.sql(ea.insert().values([
            {'question_id': 1, 'quiz_type': 2, 'exam_id': 1},
            {'question_id': 2, 'quiz_type': 2, 'exam_id': 1},
            {'question_id': 2, 'quiz_type': 2, 'exam_id': 2}
        ]))

        # Delete it and check if exam_answers table is empty
        self.sql(e.delete().where(e.c.id == 1))

        # As a result there must be one answer for exam 2
        res = self.sql(ea.select()).fetchall()
        self.assertEqual(1, len(res))
        self.assertEqual(2, res[0][ea.c.exam_id])

    # Test: udpate exam.
    # After update exam info we recalculate err percent
    # of performed exams and save it to the user_progress_snapshot.
    # NOTE: we skip 'in-progress' exams.
    def test_exams_upd(self):
        e = self.core.exams
        u = self.core.users

        # Add user to allow to update progress coef.
        sql = u.insert().values(id=3, type='student', quiz_type=2, school_id=1)
        self.sql(sql)

        # We add 3 exams and then for two of them we update
        # end time and num of errors.
        self.sql(e.insert().values([
            {'quiz_type': 2, 'user_id': 3, 'start_time': dt.utcnow()},
            {'quiz_type': 2, 'user_id': 3, 'start_time': dt.utcnow()},
            {'quiz_type': 2, 'user_id': 3, 'start_time': dt.utcnow()}
        ]))

        # Exam 1 = 2 errors
        self.sql(e.update().values(end_time=dt.utcnow(), err_count=2)
                 .where(e.c.id == 1))
        # Exam 1 = 5 errors
        self.sql(e.update().values(end_time=dt.utcnow(), err_count=7)
                 .where(e.c.id == 2))

        # Check: user_progress_snapshot entry
        # At this point we have two exams performed and one in progress.
        # First exam is passed successfully and second is not passed
        # (since we have 5 errors - 4 is maximum to pass).
        # So result progress coef will be 1/2 = 0.5
        res = self.sql('SELECT * FROM user_progress_snapshot WHERE user_id=3')
        res = res.fetchall()

        self.assertEqual(1, len(res))
        self.assertEqual(dt.utcnow().date(), res[0][2])
        self.assertEqual(0.5, res[0][3])

    # Test: insert/update guest info
    def test_guest_access(self):
        g = self.core.meta.tables['guest_access']
        s = self.core.meta.tables['guest_access_snapshot']

        # After adding guest info we also add snapshot entry.
        self.sql(g.insert().values(id=1, quiz_type=3, period_end=0))
        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(1, row[s.c.guest_id])
        self.assertEqual(3, row[s.c.quiz_type])
        self.assertTrue(dt.utcnow().date(), row[s.c.now_date])
        self.assertEqual(0, row[s.c.num_requests])

        # If guest's num_requests is changed then we count snapshot value.
        # Not trigger assumes what we increase num requests by 1.
        # This means what if num_requests is updated by any value then
        # snapshot value will be increased by 1.
        self.sql(g.update().values(num_requests=2).where(
            and_(g.c.id == 1, g.c.quiz_type == 3)))

        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(1, row[s.c.guest_id])
        self.assertEqual(3, row[s.c.quiz_type])
        self.assertTrue(dt.utcnow().date(), row[s.c.now_date])
        self.assertEqual(1, row[s.c.num_requests])

    # Test: add answers
    # If new answer is added then update number of
    # errors and answers of the topic in the
    # topic_err_current table for the current date.
    # If there is no such row in the topic_err_current then
    # create it and set number of answers to 1.
    # Otherwise, increase number of answers and update
    # number of errors.
    def test_answers_add(self):
        u = self.core.users
        a = self.core.answers
        e = self.core.meta.tables['topic_err_current']
        s = self.core.meta.tables['school_topic_err']

        # We need some users to test.
        self.sql(u.insert().values([
            {'id': 2, 'type': 'student', 'quiz_type': 2, 'school_id': 1},
            {'id': 2, 'type': 'student', 'quiz_type': 1, 'school_id': 1},
            {'id': 5, 'type': 'student', 'quiz_type': 2, 'school_id': 2}
        ]))

        # Add answer.
        self.sql(a.insert().values(user_id=2, quiz_type=2,
                 question_id=6, is_correct=False))

        # There must be one row - see above explanation.
        row = self.sql(e.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(2, row[e.c.user_id])
        self.assertEqual(2, row[e.c.quiz_type])
        self.assertEqual(1, row[e.c.topic_id])
        self.assertEqual(1, row[e.c.err_count])
        self.assertEqual(1, row[e.c.count])

        # Also school_topic_err must be updated.
        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(1, row[s.c.school_id])
        self.assertEqual(2, row[s.c.quiz_type])
        self.assertEqual(1, row[s.c.topic_id])
        self.assertEqual(1, row[s.c.err_count])
        self.assertEqual(1, row[s.c.count])

        # Add one more answer.
        self.sql(a.insert().values(user_id=2, quiz_type=2,
                 question_id=8, is_correct=True))

        # Now there still one row but num of questions = 2.
        row = self.sql(e.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(2, row[e.c.user_id])
        self.assertEqual(2, row[e.c.quiz_type])
        self.assertEqual(1, row[e.c.topic_id])
        self.assertEqual(1, row[e.c.err_count])
        self.assertEqual(2, row[e.c.count])

        # Check school_topic_err.
        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(1, row[s.c.school_id])
        self.assertEqual(2, row[s.c.quiz_type])
        self.assertEqual(1, row[s.c.topic_id])
        self.assertEqual(1, row[s.c.err_count])
        self.assertEqual(2, row[s.c.count])

    # Test: update answers
    # If answer is changed then update number of errors and current date,
    # in the topic_err_current table. If there is no row in the
    # topic_err_current then add it and set number of answers to 1.
    def test_answers_upd(self):
        u = self.core.users
        a = self.core.answers
        e = self.core.meta.tables['topic_err_current']
        s = self.core.meta.tables['school_topic_err']

        # We need some users to test.
        self.sql(u.insert().values([
            {'id': 2, 'type': 'student', 'quiz_type': 2, 'school_id': 1},
            {'id': 2, 'type': 'student', 'quiz_type': 1, 'school_id': 1},
            {'id': 5, 'type': 'student', 'quiz_type': 2, 'school_id': 2}
        ]))

        # Add answer
        self.sql(a.insert().values(user_id=2, quiz_type=2,
                 question_id=3, is_correct=False))
        # And update it
        self.sql(a.update().values(is_correct=True).where(and_(
            a.c.user_id == 2, a.c.quiz_type == 2, a.c.question_id == 3
        )))

        # Check if school_topic_err is updated.
        row = self.sql(e.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(2, row[e.c.user_id])
        self.assertEqual(2, row[e.c.quiz_type])
        self.assertEqual(1, row[e.c.topic_id])
        self.assertEqual(0, row[e.c.err_count])
        self.assertEqual(1, row[e.c.count])

        # Check school_topic_err.
        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(1, row[s.c.school_id])
        self.assertEqual(2, row[s.c.quiz_type])
        self.assertEqual(1, row[s.c.topic_id])
        self.assertEqual(0, row[s.c.err_count])
        self.assertEqual(1, row[s.c.count])

    # Test: add/update topic_err_current.
    def tees_topic_err_current(self):
        e = self.core.meta.tables['topic_err_current']
        s = self.core.meta.tables['topic_err_snapshot']

        # If new entry is added to the topic_err_current table then
        # we also update snapshot of the current state.
        self.sql(e.insert().values(user_id=2, quiz_type=3,
                 topic_id=1, err_count=2, count=4))

        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(2, row[s.c.user_id])
        self.assertEqual(3, row[s.c.quiz_type])
        self.assertEqual(1, row[s.c.topic_id])
        self.assertEqual(dt.utcnow().date(), row[s.c.now_date])
        self.assertEqual(50, row[s.c.err_percent])

        # After update we also update snapshot of the current state.
        self.sql(e.update().values(count=8).where(and_(
            e.c.user_id == 2, e.c.quiz_type == 3, e.c.topic_id == 1
        )))

        row = self.sql(s.select()).fetchall()
        self.assertEqual(1, len(row))
        row = row[0]
        self.assertEqual(2, row[s.c.user_id])
        self.assertEqual(3, row[s.c.quiz_type])
        self.assertEqual(1, row[s.c.topic_id])
        self.assertEqual(dt.utcnow().date(), row[s.c.now_date])
        self.assertEqual(25, row[s.c.err_percent])

    # Test: stored procedure for update daily snapshot of the school
    # topics statistics. This procedure will be run daily by the update
    # script. See misc/dbupdate.py.
    def test_update_school_snapshot(self):
        e = self.core.meta.tables['school_topic_err']
        s = self.core.meta.tables['school_topic_err_snapshot']

        # Insert some data to the school_topic_err
        self.sql(e.insert().values([
            {
                'school_id': 2,
                'quiz_type': 1,
                'topic_id': 3,
                'err_count': 2,
                'count': 4
            },
            {
                'school_id': 2,
                'quiz_type': 1,
                'topic_id': 5,
                'err_count': 2,
                'count': 8
            }
        ]))

        # Call the procedure.
        self.sql('call update_school_snapshot(2, 1)')

        row = self.sql(s.select()).fetchall()
        self.assertEqual(2, len(row))
        self.assertEqual(2, row[0][s.c.school_id])
        self.assertEqual(1, row[0][s.c.quiz_type])
        self.assertEqual(3, row[0][s.c.topic_id])
        self.assertEqual(dt.utcnow().date(), row[0][s.c.now_date])
        self.assertEqual(50, row[0][s.c.err_percent])

        self.assertEqual(2, row[1][s.c.school_id])
        self.assertEqual(1, row[1][s.c.quiz_type])
        self.assertEqual(5, row[1][s.c.topic_id])
        self.assertEqual(dt.utcnow().date(), row[1][s.c.now_date])
        self.assertEqual(25, row[1][s.c.err_percent])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreDbTest))
    return suite

if __name__ == '__main__':
    unittest.main()
