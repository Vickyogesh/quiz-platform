# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: create users.
class CoreSchoolTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 2}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check invalid params
    def test_createStudentBad(self):
        # Empty values
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createStudent(None, None, None, None, None)

        # Empty values again
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createStudent(1, 2, 1, None, 2)

        ### Wrong type of values

        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createStudent('', '', '', '', 'frd')

        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createStudent([], 1, 1, '22', [])

        # Add user for non-existent school
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid school ID.'):
            self.core.createStudent('a', 'b', 'v', 'b', 12)

    # Check normal situation.
    # NOTE: since by default there are 4 users then
    # new user id will be 5.
    def test_normal(self):
        info = self.core.createStudent('name1', 'surnm1', 'login1', 'pass1', 1)
        self.assertEqual(5, info['id'])
        self.assertEqual('name1', info['name'])
        self.assertEqual('surnm1', info['surname'])

    # Check creation of the school with already existent login.
    def test_duplicates(self):
        self.core.createStudent('Bob', 'Marley', 'somelogin', 'pass', 1)

        with self.assertRaisesRegexp(QuizCoreError, 'Already exists.'):
            self.core.createStudent('Bob', 'Marley', 'somelogin', 'pass', 1)

    # Check: list of students with wrong data.
    def test_studentListBad(self):
        # Non-existent id
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid school ID.'):
            self.core.getStudentList(1000)

        # Not a school id
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid school ID.'):
            self.core.getStudentList(3)

    # Check: list of students.
    def test_studentList(self):
        # By default we have one school.
        # See misc/dbtools.py
        info = self.core.getStudentList(1)

        students = info['students']
        self.assertEqual(3, len(students))

        student = students[0]
        self.assertEqual(1, student['id'])
        self.assertEqual('Chuck Norris School', student['name'])
        self.assertEqual('', student['surname'])
        self.assertEqual('chuck@norris.com-guest', student['login'])
        self.assertEqual('guest', student['type'])

        student = students[1]
        self.assertEqual(3, student['id'])
        self.assertEqual('Test2', student['name'])
        self.assertEqual('User2', student['surname'])
        self.assertEqual('testuser2', student['login'])
        self.assertEqual('student', student['type'])

        student = students[2]
        self.assertEqual(4, student['id'])
        self.assertEqual('Test', student['name'])
        self.assertEqual('User', student['surname'])
        self.assertEqual('testuser', student['login'])
        self.assertEqual('student', student['type'])

    # Check: delete student. Here we test how triggres works actually.
    # Triggres are created in the _createFuncs() (misc/dbtools.py):
    #   * on_del_school
    #   * on_del_user
    #   * on_del_exam
    def test_deleteStudent(self):
        # Check non-existent school
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid school ID.'):
            self.core.deleteStudent(100, 1)

        # Check non-existent user
        with self.assertRaisesRegexp(QuizCoreError, 'Unknown student.'):
            self.core.deleteStudent(1, 100)

        # Check user from another school
        with self.assertRaisesRegexp(QuizCoreError, 'Unknown student.'):
            self.core.deleteStudent(1, 2)

        # create exam and answer some questions.
        # See core/test_exam.py for more info.
        info = self.core.createExam(3, 'it')
        questions = [q['id'] for q in info['questions']]
        questions = list(sorted(questions))
        answers = [1] * 40
        answers[:5] = [0] * 5  # make some errors
        self.core.saveExam(1, questions, answers)

        # Put some quiz answers
        # See core/test_quiz.py for more info.
        self.core.saveQuiz(3, 1, [10, 12, 13], [1, 1, 0])

        # Now we must have rows in the following tables:
        # exams, exam_answers, topics_stat, errors, quiz_answers;
        # and also in schools, users, guest_access.
        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from exam_answers").fetchone()
        self.assertEqual(40, res[0])
        res = self.engine.execute("SELECT count(*) from topic_err_current").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from topic_err_snapshot").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from answers").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from quiz_answers").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from users").fetchone()
        self.assertEqual(4, res[0])

        # Now we can delete school and see
        # if all generated date will be removed too.
        self.core.deleteStudent(1, 3)

        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from exam_answers").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from topic_err_current").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from topic_err_snapshot").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from answers").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from quiz_answers").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from users").fetchone()
        self.assertEqual(3, res[0])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreSchoolTest))
    return suite

if __name__ == '__main__':
    unittest.main()
