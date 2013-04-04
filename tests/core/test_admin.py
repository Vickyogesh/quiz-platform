# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
import hashlib
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: create school.
class CoreAdminTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 2}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine, drop_users=True)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check invalid params
    def test_createSchoolBad(self):
        # Empty values
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createSchool(None, None, None)

        # Empty values again
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createSchool(1, 2, None)

        ### Wrong type of values

        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createSchool('', '', '')

        with self.assertRaisesRegexp(QuizCoreError, 'Invalid parameters.'):
            self.core.createSchool(1, 1, '22')

    def _create_digest(self, username):
        m = hashlib.md5()
        m.update('%s:guest' % username)
        return m.hexdigest()

    # Check normal situation.
    def test_normal(self):
        info = self.core.createSchool('someschool', 'somelogin', 'pass')
        self.assertEqual(1, info['id'])

        res = self.engine.execute('SELECT * from schools')
        res = res.fetchone()
        self.assertEqual(1, res['id'])
        self.assertEqual('someschool', res['name'])
        self.assertEqual('somelogin', res['login'])

        # School guest must be created additionally to the school.
        res = self.engine.execute('SELECT * from users WHERE type="guest"')
        res = res.fetchone()
        self.assertEqual(1, res['id'])
        self.assertEqual(1, res['school_id'])
        self.assertEqual('someschool', res['name'])
        self.assertEqual('', res['surname'])
        self.assertEqual('guest', res['type'])
        self.assertEqual('somelogin-guest', res['login'])
        pwd = self._create_digest('somelogin-guest')
        self.assertEqual(pwd, res['passwd'])

    # Check: creation of the school with already existent login.
    def test_duplicates(self):
        self.core.createSchool('someschool', 'somelogin', 'pass')
        with self.assertRaisesRegexp(QuizCoreError, 'Already exists.'):
            self.core.createSchool('someschool', 'somelogin', 'pass')

    # Check: get list of schools.
    def test_schoolList(self):
        # Test empty
        info = self.core.getSchoolList()
        self.assertEqual(0, len(info['schools']))

        # Check list
        self.core.createSchool('someschool1', 'somelogin1', 'pass')
        self.core.createSchool('someschool2', 'somelogin2', 'pass')
        self.core.createSchool('someschool3', 'somelogin3', 'pass')

        info = self.core.getSchoolList()
        info = info['schools']
        self.assertEqual(3, len(info))

        school = info[0]
        self.assertEqual(1, school['id'])
        self.assertEqual('someschool1', school['name'])
        self.assertEqual('somelogin1', school['login'])

        # NOTE: next schools will have ids = 3, 5
        # since there are also guest users.
        school = info[1]
        self.assertEqual(2, school['id'])
        self.assertEqual('someschool2', school['name'])
        self.assertEqual('somelogin2', school['login'])

        school = info[2]
        self.assertEqual(3, school['id'])
        self.assertEqual('someschool3', school['name'])
        self.assertEqual('somelogin3', school['login'])

    # Check: delete school. Here we test how triggres works actually.
    # Triggres are created in the _createFuncs() (misc/dbtools.py):
    #   * on_del_school
    #   * on_del_user
    #   * on_del_exam
    def test_deleteSchool(self):
        # Check non-existent scholl delete
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid school ID.'):
            self.core.deleteSchool(1)

        # Add one school and fill with some data
        self.core.createSchool('school', 'login', 'pass')

        # We have guest so let's use it: create exam and answer some questions.
        # See core/test_exam.py for more info.
        info = self.core.createExam(1, 'it')
        questions = [q['id'] for q in info['questions']]
        questions = list(sorted(questions))
        answers = [1] * 40
        answers[:5] = [0] * 5  # make some errors
        self.core.saveExam(1, questions, answers)

        # Put some quiz answers
        # See core/test_quiz.py for more info.
        self.core.saveQuiz(1, 1, [10, 12, 13], [1, 1, 0])

        # Now we must have rows in the following tables:
        # exams, exam_answers, topics_stat, answers, quiz_answers;
        # and also in schools, users, guest_access.
        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from exam_answers").fetchone()
        self.assertEqual(40, res[0])
        res = self.engine.execute("SELECT count(*) from topics_stat").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from answers").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from quiz_answers").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from schools").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from users").fetchone()
        self.assertLessEqual(1, res[0])
        res = self.engine.execute("SELECT count(*) from guest_access").fetchone()
        self.assertLessEqual(1, res[0])

        # Now we can delete school and see
        # if all generated date will be removed too.
        self.core.deleteSchool(1)

        res = self.engine.execute("SELECT count(*) from exams").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from exam_answers").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from topics_stat").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from answers").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from quiz_answers").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from schools").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from users").fetchone()
        self.assertEqual(0, res[0])
        res = self.engine.execute("SELECT count(*) from guest_access").fetchone()
        self.assertEqual(0, res[0])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreAdminTest))
    return suite

if __name__ == '__main__':
    unittest.main()
