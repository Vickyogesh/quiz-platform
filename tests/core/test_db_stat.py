# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri
from quiz.core.core import QuizCore


# TODO: implement me.
class DbStatTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'admin_password': '', 'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.engine = self.core.engine
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE exams;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")
        self.engine.execute("TRUNCATE TABLE exams_stat;")

    def tearDown(self):
        self.engine.execute("TRUNCATE TABLE answers;")
        self.engine.execute("TRUNCATE TABLE exams;")
        self.engine.execute("TRUNCATE TABLE topics_stat;")
        self.engine.execute("TRUNCATE TABLE exams_stat;")


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DbStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()
