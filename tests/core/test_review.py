# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError


# Test: get error review and save answers.
class CoreReviewTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    # Check: get review for invalid user - must return empty list
    def test_getWrongUser(self):
        review = self.core.getErrorReview(1000, 'it')
        self.assertEqual(0, len(review['questions']))

    # Check: get review for the correct user
    # but answers table is empty - must return empty list
    def test_getEmpty(self):
        review = self.core.getErrorReview(1, 'it')
        self.assertEqual(0, len(review['questions']))

    # Check: fill some answers and get wrong ones.
    def test_get(self):
        # Put 3 wrong answers.
        self.engine.execute("""INSERT INTO answers values
                            (1, 3, 0), (1, 4, 0), (1, 5, 0)""")

        # Error review must contain only questions with ids 3, 4, 5.
        review = self.core.getErrorReview(1, 'it')
        questions = review['questions']
        questions = sorted([q['id'] for q in questions])
        self.assertEqual([3, 4, 5], questions)

    # Check: save wrong data - currently answers will be saved
    # even for wrong users.
    def test_saveWrong(self):
        # Wrong user
        self.core.saveErrorReview(100, [1], [1])

        # Empty questions
        with self.assertRaisesRegexp(QuizCoreError, 'Parameters length mismatch.'):
            self.core.saveErrorReview(1, [], [1])

        # Empty answers
        with self.assertRaisesRegexp(QuizCoreError, 'Parameters length mismatch.'):
            self.core.saveErrorReview(1, [1], [])

        # Empty all
        with self.assertRaisesRegexp(QuizCoreError, 'Empty list.'):
            self.core.saveErrorReview(1, [], [])

        # Wrong questions
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid value.'):
            self.core.saveErrorReview(1, ['b', 1], [1, 1])

        # Wrong answers
        with self.assertRaisesRegexp(QuizCoreError, 'Invalid value.'):
            self.core.saveErrorReview(1, [1, 1], ['b', 1])

    # Check: normal save
    def test_save(self):
        # set initial errors
        self.engine.execute("""INSERT INTO answers values
                            (1, 1, 0), (1, 2, 0), (1, 3, 0), (1, 4, 0), (1, 5, 0), (1, 6, 0)""")

        self.core.saveErrorReview(1, [1, 2, 3, 4, 5], [1, 1, 0, 0, 0])

        res = self.engine.execute("SELECT question_id FROM answers where is_correct=0")
        data = [row[0] for row in res]
        data = list(sorted(data))

        self.assertEqual(3, data[0])
        self.assertEqual(4, data[1])
        self.assertEqual(5, data[2])
        self.assertEqual(6, data[3])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreReviewTest))
    return suite

if __name__ == '__main__':
    unittest.main()
