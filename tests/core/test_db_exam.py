# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from datetime import datetime, timedelta
from collections import namedtuple
from quiz.exceptions import QuizCoreError
from tests_common import db_uri
from quiz.db.quizdb import QuizDb

ExamInfo = namedtuple('ExamInfo', 'id user_id start end err_count')


# Test: generate exam, save exam.
class DbExamTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.db = QuizDb(self)
        self.questions = self.db.questions
        self.engine = self.db.engine
        self.engine.execute("TRUNCATE TABLE exams_stat;")
        self.engine.execute("TRUNCATE TABLE exams;")
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")

    def tearDown(self):
        self.engine.execute("TRUNCATE TABLE exams_stat;")
        self.engine.execute("TRUNCATE TABLE exams;")
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")

    # Check if generated ids are in correct question ranges.
    # See ExamMixin.__generate_idList() for more info.
    def test_questionIds(self):
        ids = self.db._ExamMixin__generate_idList()
        ids = list(sorted(ids))

        # Get ranges:
        # | priority | min_id  |  max_id
        # |----------+-----+------
        # |     1    |    1    |  100
        # |     2    |   101   |  200
        chapters_info = self.db._ExamMixin__stmt_ch_info.execute()
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
        info = self.db.createExam(1, 'it')

        # Check return value
        # there must be 'exam' and 'question' fields.

        ### Check exam

        exam = info['exam']
        self.assertTrue('id' in exam)
        self.assertTrue('expires' in exam)

        # Check expiration date
        # format: 2013-03-21 12:04:12
        expires = datetime.strptime(exam['expires'], "%Y-%m-%d %H:%M:%S")

        # now and expires must be almost the same
        # and we just check if delta between them is less than 5 sec.
        now = datetime.utcnow() + timedelta(hours=3)
        delta = now - expires
        delta = abs(delta.total_seconds())
        self.assertTrue(delta < 5)

        ### Check questions

        questions = info['questions']
        self.assertEqual(40, len(questions))

        # Pick random question to check it's fields
        # Note: 'image' and 'image_bis' may be absent
        # if values are null for these fields. So we
        # do not check them.
        question = questions[20]
        self.assertTrue('id' in question)
        self.assertTrue('text' in question)
        self.assertTrue('answer' in question)

    # Test if for new exam 'exams' and 'exams_stat' tables are filled
    def test_newDBTables(self):
        # Make sure there is no exams
        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(0, res[0])

        res = self.engine.execute("SELECT count(*) from exams_stat").fetchone()
        self.assertEqual(0, res[0])

        info = self.db.createExam(1, 'it')

        # After new exam generation there must be one entry in the
        # 'exams' table which describes exam and also 'exams_stat'
        # must contain 40 exam questions.
        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from exams_stat").fetchone()
        self.assertEqual(40, res[0])

        ### Check exam metadata

        res = self.engine.execute("SELECT * from exams").fetchone()
        exam_id = res[0]
        user_id = res[1]
        start = res[2]
        end = res[3]
        err_count = res[4]

        self.assertEqual(info['exam']['id'], exam_id)
        self.assertEqual(1, user_id)
        self.assertEqual(0, err_count)
        self.assertEqual(None, end)

        now = datetime.utcnow()
        delta = now - start
        delta = abs(delta.total_seconds())
        self.assertTrue(delta < 5)

        ### Check exam questions

        res = self.engine.execute(
            "SELECT question_id,is_correct from exams_stat WHERE exam_id="
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
        try:
            self.db.saveExam(1, [], [])
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid exam ID.', err)

        # We have to create exam before continue testing
        info = self.db.createExam(1, 'it')
        exam_id = info['exam']['id']

        # Try to save with wrong number of answers
        # NOTE: answers length will be checked before questions.
        try:
            self.db.saveExam(exam_id, [], [])
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Wrong number of answers.', err)

        # Try to save with wrong number of questions
        try:
            self.db.saveExam(exam_id, [], [0] * 40)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Parameters length mismatch.', err)

        # Try to save with wrong questions' IDs
        try:
            self.db.saveExam(exam_id, [0] * 40, [0] * 40)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid question ID.', err)

        # Make exam expired and try to save answers
        # NOTE: expiration date will be checked before questions
        # validation so we can pass fake values.
        try:
            self.engine.execute("UPDATE exams SET start_time='1999-01-12'")
            self.db.saveExam(exam_id, [0] * 40, [0] * 40)
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Exam is expired.', err)

    # Helper function to get exam metadate dirrectly from the DB.
    def _getExamInfo(self, id):
        res = self.engine.execute("SELECT * FROM exams WHERE id=" + str(id))
        res = res.fetchone()
        return ExamInfo(id=res[0], user_id=res[1], start=res[2],
                        end=res[3], err_count=res[4])

    # Check normal exam save
    def test_save(self):
        info = self.db.createExam(1, 'it')
        exam_id = info['exam']['id']
        questions = [q['id'] for q in info['questions']]
        questions = list(sorted(questions))

        # Make 5 errors
        answers = [1] * 40
        answers[:5] = [0] * 5
        self.db.saveExam(exam_id, questions, answers)

        ### Check answers

        res = self.engine.execute(
            "SELECT question_id,is_correct from exams_stat WHERE exam_id="
            + str(exam_id))

        for row, a in zip(res, answers):
            self.assertEqual(a, row[1])

        ### Check exam metadata
        # We don't check start time
        exam = self._getExamInfo(exam_id)
        self.assertEqual(1, exam.user_id)
        self.assertEqual(5, exam.err_count)

        now = datetime.utcnow()
        delta = abs((now - exam.end).total_seconds())
        self.assertTrue(delta < 2)

    # Check exam info API
    def test_statusNew(self):
        # Try to get infor for non-existent exam
        try:
            self.db.getExamInfo(1, 'it')
        except QuizCoreError as e:
            err = e.message
        self.assertEqual('Invalid exam ID.', err)

        # Check status for the fresh exam
        info = self.db.createExam(1, 'it')
        exam_id = info['exam']['id']
        exam_questions = info['questions']

        info = self.db.getExamInfo(exam_id, 'it')
        exam = info['exam']
        student = info['student']
        questions = info['questions']

        # Check student
        self.assertEqual(1, student['id'])
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

    # Helper function to create exam & save answers.
    # Returns result exam info
    def _passExam(self, answers):
        info = self.db.createExam(1, 'it')
        exam_id = info['exam']['id']
        questions = list(sorted([q['id'] for q in info['questions']]))

        self.db.saveExam(exam_id, questions, answers)
        return self.db.getExamInfo(exam_id, 'it')

    # Check passed status.
    # We can make up to 4 errors
    def test_statusPassed(self):
        # Pass with no errors and check status:
        # Since we made no errors then exam must be passed.
        info = self._passExam([1] * 40)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(0, exam['errors'])

        # Pass with 1 error and check status.
        answers = [1] * 40
        answers[0] = 0
        info = self._passExam(answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(1, exam['errors'])

        # Pass with 2 errors and check status.
        answers = [1] * 40
        answers[:2] = [0, 0]
        info = self._passExam(answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(2, exam['errors'])

        # Pass with 3 errors and check status.
        answers = [1] * 40
        answers[:3] = [0, 0, 0]
        info = self._passExam(answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(3, exam['errors'])

        # Pass with 3 errors and check status.
        answers = [1] * 40
        answers[:4] = [0, 0, 0, 0]
        info = self._passExam(answers)
        exam = info['exam']
        self.assertEqual('passed', exam['status'])
        self.assertEqual(4, exam['errors'])

    # Check failed status (more than 4 errors).
    def test_statusFailed(self):
        # 5 errors.
        answers = [1] * 40
        answers[0:5] = [0] * 5
        info = self._passExam(answers)
        exam = info['exam']
        self.assertEqual('failed', exam['status'])
        self.assertEqual(5, exam['errors'])

        # 15 errors.
        answers = [1] * 40
        answers[0:15] = [0] * 15
        info = self._passExam(answers)
        exam = info['exam']
        self.assertEqual('failed', exam['status'])
        self.assertEqual(15, exam['errors'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DbExamTest))
    return suite

if __name__ == '__main__':
    unittest.main()
