# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from tests_common import db_uri
#from sqlalchemy import select, text
from quiz.db.quizdb import QuizDb


# TODO: add tests explanations.
class DbExamTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.db = QuizDb(self)
        self.stat = self.db.quiz_stat
        self.questions = self.db.questions
        self.conn = self.db.conn
        # self.conn.execute("DELETE from quiz_stat;")

    def tearDown(self):
        # self.conn.execute("DELETE from quiz_stat;")
        self.conn.close()

    # Validate each value in the list - check ranges
    def test_getIdList(self):
        for x in xrange(3):
            lst = self.db._ExamMixin__generate_idList()
            self.assertEqual(40, len(lst))

            lst = iter(sorted(lst))
            res = self.conn.execute(self.db._ExamMixin__stmt_ch_info)
            for row in res:
                first = row[1]
                last = row[2]

                for i in xrange(row[0]):
                    id = lst.next()
                    self.assertTrue(first <= id <= last)

    def test_getExam(self):
        exam = self.db.getExam('it')
        self.assertEqual(40, len(exam))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DbExamTest))
    return suite

if __name__ == '__main__':
    unittest.main()
