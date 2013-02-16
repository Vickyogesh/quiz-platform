# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
import tests_common as cfg
from quiz.db import QuizDb


class CoreTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': cfg.db_uri, 'verbose': 'False'}
        self.db = QuizDb(self)

    def test_getInfo(self):
        info = self.db.getInfo('testuser',
                               'b929d0c46cf5609e0104e50d301b0b8b482e9bfc')
        self.assertEqual('aa4a5443cb91ee1810785314651e5dd1', info['passwd'])
        self.assertEqual(1, info['user_id'])
        self.assertEqual(3, info['app_id'])
        self.assertEqual('student', info['type'])

    def test_getQuiz(self):
        quiz = self.db.getQuiz(1, 'it', 40)
        self.assertEqual(40, len(quiz))

        quiz = self.db.getQuiz(100, 'it', 40)
        self.assertEqual(0, len(quiz))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreTest))
    return suite

if __name__ == '__main__':
    unittest.main()
