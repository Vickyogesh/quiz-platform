# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from datetime import datetime, timedelta
from collections import namedtuple
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError

ExamInfo = namedtuple('ExamInfo', 'id user_id start end err_count')


# Helper function to create exam & save answers.
# Returns result exam info
def pass_exam(tst, answers):
    info = tst.core.createExam(4, 'it')
    exam_id = info['exam']['id']
    questions = list(sorted([q['id'] for q in info['questions']]))

    tst.core.saveExam(exam_id, questions, answers)
    return tst.core.getExamInfo(exam_id, 'it')


# Test: generate exam, save exam, exam's errors counting.
class CoreExamTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.questions = self.core.questions
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check if generated ids are in correct question ranges.
    # See ExamMixin.__generate_idList() for more info.
    def test_questionIds(self):
        norm, high = self.core._ExamMixin__generate_idList()
        self.assertEqual(25, len(norm))
        self.assertEqual(15, len(high))
        ids = list(sorted(norm+high))

        # Get ranges:
        # | priority | min_id  |  max_id
        # |----------+-----+------
        # |     1    |    1    |  100
        # |     2    |   101   |  200
        chapters_info = self.core._ExamMixin__stmt_ch_info.execute()
        index = 0

        # Check if item in ids is in correct range.
        for row in chapters_info:
            num_questions_in_range = row[0]
            min_id = row[1]
            max_id = row[2]
            for x in xrange(num_questions_in_range):
                self.assertTrue(min_id <= ids[index] <= max_id)
                index += 1

    # Test id list construction multiple times
    def test_questionIdsMany(self):
        for x in xrange(10):
            self.test_questionIds()

    # Test new exam fields.
    def test_newFields(self):
        info = self.core.createExam(3, 'it')

        # Check return value
        # there must be 'exam' and 'question' fields.

        ### Check exam

        exam = info['exam']
        self.assertIn('id', exam)
        self.assertIn('expires', exam)

        # Check expiration date
        # format: 2013-03-21 12:04:12
        expires = datetime.strptime(exam['expires'], "%Y-%m-%d %H:%M:%S")

        # now and expires must be almost the same
        # and we just check if delta between them is less than 5 sec.
        now = datetime.utcnow() + timedelta(hours=3)
        delta = now - expires
        delta = abs(delta.total_seconds())
        self.assertTrue(delta <= 5)

        ### Check questions

        questions = info['questions']
        self.assertEqual(40, len(questions))

        # Pick random question to check it's fields
        # Note: 'image' and 'image_bis' may be absent
        # if values are null for these fields. So we
        # do not check them.
        question = questions[20]
        self.assertIn('id', question)
        self.assertIn('text', question)
        self.assertIn('answer', question)

    # Test if for new exam 'exams' and 'exams_stat' tables are filled
    def test_newDBTables(self):
        # Make sure there is no exams
        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(0, res[0])

        res = self.engine.execute("SELECT count(*) from exam_answers").fetchone()
        self.assertEqual(0, res[0])

        res = self.engine.execute("SELECT count(*) from answers").fetchone()
        self.assertEqual(0, res[0])

        info = self.core.createExam(3, 'it')

        # After new exam generation there must be one entry in the
        # 'exams' table which describes exam and also 'exam_answers'
        # must contain 40 exam questions, but 'answers' will not be updated.
        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(1, res[0])

        res = self.engine.execute("SELECT count(*) from exam_answers").fetchone()
        self.assertEqual(40, res[0])

        res = self.engine.execute("SELECT count(*) from answers").fetchone()
        self.assertEqual(0, res[0])

        ### Check exam metadata

        res = self.engine.execute("SELECT * from exams").fetchone()
        exam_id = res[0]
        user_id = res[1]
        start = res[2]
        end = res[3]
        err_count = res[4]

        self.assertEqual(info['exam']['id'], exam_id)
        self.assertEqual(3, user_id)
        self.assertEqual(0, err_count)
        self.assertEqual(None, end)

        now = datetime.utcnow()
        delta = now - start
        delta = abs(delta.total_seconds())
        self.assertTrue(delta <= 5)

        ### Check exam questions

        res = self.engine.execute(
            "SELECT question_id,is_correct from exam_answers WHERE exam_id="
            + str(exam_id))

        table_questions = []
        answers = []
        for row in res:
            table_questions.append(row[0])
            answers.append(row[1])
        table_questions = list(sorted(table_questions))

        questions = [q['id'] for q in info['questions']]
        questions = list(sorted(questions))

        self.assertEqual(questions, table_questions)

        # every answer must be wrong by default
        self.assertEqual(answers, [0] * 40)

    # Check exam saving with wrong data
    def test_saveWrong(self):
        # try to save non-existent exam
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid exam ID.'):
            self.core.saveExam(1, [], [])

        # We have to create exam before continue testing
        info = self.core.createExam(3, 'it')
        exam_id = info['exam']['id']

        # Try to save with wrong number of answers
        # NOTE: answers length will be checked before questions.
        with self.assertRaisesRegexp(QuizCoreError, 'Wrong number of answers.'):
            self.core.saveExam(exam_id, [], [])

        # Try to save with wrong number of questions
        with self.assertRaisesRegexp(QuizCoreError, 'Parameters length mismatch.'):
            self.core.saveExam(exam_id, [], [0] * 40)

        # Try to save with wrong questions' IDs
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid question ID.'):
            self.core.saveExam(exam_id, [0] * 40, [0] * 40)

        # Make exam expired and try to save answers
        # NOTE: expiration date will be checked before questions
        # validation so we can pass fake values.
        with self.assertRaisesRegexp(QuizCoreError, 'Exam is expired.'):
            self.engine.execute("UPDATE exams SET start_time='1999-01-12'")
            self.core.saveExam(exam_id, [0] * 40, [0] * 40)

    # Helper function to get exam metadate dirrectly from the DB.
    def _getExamInfo(self, id):
        res = self.engine.execute("SELECT * FROM exams WHERE id=" + str(id))
        res = res.fetchone()
        return ExamInfo(id=res[0], user_id=res[1], start=res[2],
                        end=res[3], err_count=res[4])

    # Check normal exam save
    def test_save(self):
        info = self.core.createExam(3, 'it')
        exam_id = info['exam']['id']
        questions = [q['id'] for q in info['questions']]
        questions = list(sorted(questions))

        # Make 5 errors
        answers = [1] * 40
        answers[:5] = [0] * 5
        self.core.saveExam(exam_id, questions, answers)

        ### Check exam answers

        res = self.engine.execute(
            "SELECT question_id,is_correct from exam_answers WHERE exam_id="
            + str(exam_id))

        for row, a in zip(res, answers):
            self.assertEqual(a, row[1])

        ### Check exam metadata
        # We don't check start time
        exam = self._getExamInfo(exam_id)
        self.assertEqual(3, exam.user_id)
        self.assertEqual(5, exam.err_count)

        now = datetime.utcnow()
        delta = abs((now - exam.end).total_seconds())
        self.assertTrue(delta <= 5)

        ### Check errors
        res = self.engine.execute("SELECT question_id from answers where is_correct=FALSE")
        err_questions = [row[0] for row in res]
        err_questions = list(sorted(err_questions))
        self.assertEqual(questions[0:5], err_questions)

    # Check exam info API
    def test_statusNew(self):
        # Try to get infor for non-existent exam
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid exam ID.'):
            self.core.getExamInfo(1, 'it')

        # Check status for the fresh exam
        info = self.core.createExam(4, 'it')
        exam_id = info['exam']['id']
        exam_questions = info['questions']

        info = self.core.getExamInfo(exam_id, 'it')
        exam = info['exam']
        student = info['student']
        questions = info['questions']

        # Check student
        self.assertEqual(4, student['id'])
        self.assertEqual('Test', student['name'])
        self.assertEqual('User', student['surname'])

        # Check questions
        q1 = list(sorted([q['id'] for q in exam_questions]))
        q2 = list(sorted([q['id'] for q in questions]))
        self.assertEqual(q1, q2)

        # Check exam metadata
        real_exam = self._getExamInfo(exam_id)
        self.assertEqual(real_exam.id, exam['id'])
        self.assertEqual(str(real_exam.start), exam['start'])
        self.assertEqual(str(real_exam.end), exam['end'])
        self.assertEqual(real_exam.err_count, exam['errors'])

        # Since we just created the exam then it's status must be 'in-progress'
        self.assertEqual('in-progress', exam['status'])

    # Check passed status.
    # We can make up to 4 errors
    def test_statusPassed(self):
        # Pass with no errors and check status:
        # Since we made no errors then exam must be passed.
        info = pass_exam(self, [1] * 40)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(0, exam['errors'])

        # Pass with 1 error and check status.
        answers = [1] * 40
        answers[0] = 0
        info = pass_exam(self, answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(1, exam['errors'])

        # Pass with 2 errors and check status.
        answers = [1] * 40
        answers[:2] = [0, 0]
        info = pass_exam(self, answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(2, exam['errors'])

        # Pass with 3 errors and check status.
        answers = [1] * 40
        answers[:3] = [0, 0, 0]
        info = pass_exam(self, answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(3, exam['errors'])

        # Pass with 3 errors and check status.
        answers = [1] * 40
        answers[:4] = [0, 0, 0, 0]
        info = pass_exam(self, answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(4, exam['errors'])

    # Check failed status (more than 4 errors).
    def test_statusFailed(self):
        # 5 errors.
        answers = [1] * 40
        answers[0:5] = [0] * 5
        info = pass_exam(self, answers)
        exam = info['exam']
        self.assertEqual('failed', exam['status'])
        self.assertEqual(5, exam['errors'])

        # 15 errors.
        answers = [1] * 40
        answers[0:15] = [0] * 15
        info = pass_exam(self, answers)
        exam = info['exam']
        self.assertEqual('failed', exam['status'])
        self.assertEqual(15, exam['errors'])


# Test: exam statistics.
class CoreExamStatTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.questions = self.core.questions
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check: progress_coef if only one exam is passed (successfully).
    def test_updateCoefOneOk(self):
        # Pass exam with no errors and check progress_coef:
        # Since we made no errors then progress_coef must be 0.
        # This means what there is 0% of errors, ie all exams is passed.
        pass_exam(self, [1] * 40)

        sql = "SELECT progress_coef from users where id=4"
        row = self.engine.execute(sql).fetchone()
        self.assertEqual(0, row[0])

    # Check: progress_coef if only one exam is passed (failed).
    def test_updateCoefOneFail(self):
        pass_exam(self, [1] * 20 + [0] * 20)

        sql = "SELECT progress_coef from users where id=4"
        row = self.engine.execute(sql).fetchone()
        self.assertEqual(1, row[0])

    # Check: progress_coef with exam which is in progress.
    def test_updateCoefProgressExam(self):
        self.core.createExam(4, 'it')

        # Since 'in-progress' exams are skipped then
        # progress_coef will be -1.
        sql = "SELECT progress_coef from users where id=4"
        row = self.engine.execute(sql).fetchone()
        self.assertEqual(-1, row[0])

    # Check: progress_coef if two exams are passed (failed & successfully).
    def test_updateCoefTwoExams(self):
        pass_exam(self, [1] * 40)
        pass_exam(self, [1] * 20 + [0] * 20)

        sql = "SELECT progress_coef from users where id=4"
        row = self.engine.execute(sql).fetchone()
        self.assertAlmostEqual(0.5, row[0], 1)

    # Check: progress_coef for all exam types.
    def test_updateCoef(self):
        # Pass one exam, fail one exam, and create 'in-progress' exam.
        pass_exam(self, [1] * 40)
        pass_exam(self, [1] * 20 + [0] * 20)
        self.core.createExam(4, 'it')

        # We must have 50% of errors.
        sql = "SELECT progress_coef from users where id=4"
        row = self.engine.execute(sql).fetchone()
        self.assertAlmostEqual(0.5, row[0], 1)

        # Pass one more exam, so ~33% of errors
        # 1 failed and 2 passed, 3 exams overall (we skip 'in-progress') = 1/3
        pass_exam(self, [1] * 40)
        row = self.engine.execute(sql).fetchone()
        self.assertAlmostEqual(0.33, row[0], 2)

        # Fail exam
        # 2 failed and 2 passed, total 4 = 2/2
        pass_exam(self, [1] * 20 + [0] * 20)
        row = self.engine.execute(sql).fetchone()
        self.assertAlmostEqual(0.5, row[0], 1)

        # 3 failed and 2 passed, total 5 = 3/5
        pass_exam(self, [1] * 20 + [0] * 20)
        row = self.engine.execute(sql).fetchone()
        self.assertAlmostEqual(0.6, row[0], 1)

    # Check: exam snapshot update.
    def test_snapshot(self):
        # update current coef and cjeck snapshot
        sql = "UPDATE users SET progress_coef=0.23 WHERE id=4"
        self.engine.execute(sql)

        # Since we cleanup user_progress_snapshot in setUp()
        # then we'll have only one row
        sql = "SELECT * FROM user_progress_snapshot WHERE user_id=4"
        res = self.engine.execute(sql).fetchall()
        self.assertEqual(1, len(res))
        row = res[0]

        self.assertEqual(4, row['user_id'])
        self.assertEqual(datetime.utcnow().date(), row['now_date'])
        self.assertAlmostEqual(0.23, row['progress_coef'], 2)

        # One more change
        sql = "UPDATE users SET progress_coef=0.25 WHERE id=4"
        self.engine.execute(sql)

        # Since we cleanup user_progress_snapshot in setUp()
        # then we'll have only one row
        sql = "SELECT * FROM user_progress_snapshot WHERE user_id=4"
        res = self.engine.execute(sql).fetchall()
        self.assertEqual(1, len(res))
        row = res[0]

        self.assertEqual(4, row['user_id'])
        self.assertEqual(datetime.utcnow().date(), row['now_date'])
        self.assertAlmostEqual(0.25, row['progress_coef'], 2)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreExamTest))
    suite.addTest(unittest.makeSuite(CoreExamStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()