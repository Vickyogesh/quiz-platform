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
        self.main = {'guest_allowed_requests': 2}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check: delete student. Here we test how triggres works actually.
    # Triggres are created in the _createFuncs() (misc/dbtools.py):
    #   * on_del_school
    #   * on_del_user
    #   * on_del_exam
    def test_deleteStudent(self):
        # create exam and answer some questions.
        # See core/test_exam.py for more info.
        info = self.core.createExam(1, 3, 'it')
        questions = [q['id'] for q in info['questions']]
        questions = list(sorted(questions))
        answers = [1] * 40
        answers[:5] = [0] * 5  # make some errors
        self.core.saveExam(1, questions, answers)

        # Put some quiz answers
        # See core/test_quiz.py for more info.
        self.core.saveQuiz(1, 3, 1, [10, 12, 13], [1, 1, 0])

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
        self.assertEqual(5, res[0])

        # Now we can delete school and see
        # if all generated date will be removed too.
        self.core.deleteStudent(3)

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
