import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

import unittest
from quiz.core2.models import db
from test_common import app, truncate_answers


# 1 - b2011, 3 - b2013, 50 - b
# 2 - cqc
# 4 - scooter
# 5 - 11 - truck
# 60 - 66 - revisioni

class QuizTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        with self.app.app_context():
            from quiz.core2.exam.logic import ExamCore
            from quiz.core2.meta import meta
            self.meta = meta
            self.core = ExamCore()
            truncate_answers(db.engine)

    def tearDown(self):
        with self.app.app_context():
            truncate_answers(db.engine)

    def test_get_b_exam(self):
        with self.app.app_context():
            exam = self.core.createExam(50, 1, 'it')

            self.assertEqual(self.meta['b']['exam_meta']['num_questions'], len(exam['questions']))

    def test_get_am_exam(self):
        with self.app.app_context():
            exam = self.core.createExam(4, 1, 'it')

            self.assertEqual(self.meta['am']['exam_meta']['num_questions'], len(exam['questions']))

    def test_get_cqc_exam(self):
        with self.app.app_context():
            exam = self.core.createExam(2, 1, 'it', examType='generale')

            self.assertEqual(self.meta['cqc']['exam_meta']['num_questions'], len(exam['questions']))

    def test_get_cde_exam(self):
        with self.app.app_context():
            for quiz_type in range(5, 12):
                exam = self.core.createExam(quiz_type, 1, 'it')
                self.assertEqual(self.meta['cde']['exam_meta'][quiz_type]['num_questions'], len(exam['questions']))

    # FIXME bug with request context
    # def test_get_rev_exam(self):
    #     with self.app.app_context():
    #         for quiz_type in range(60, 67):
    #             exam = self.core.createExam(quiz_type, 1, 'it')
    #             self.assertTrue(len(exam['questions']) > 0)


    def test_save_exam(self):
        with self.app.app_context():
            exam = self.core.createExam(50, 1, 'it')

            num_questions = self.meta['b']['exam_meta']['num_questions']
            exam_id = exam['exam']['id']
            question_ids = [int(i['id']) for i in exam['questions']]
            answers = [1 if a % 2 == 0 else 0 for a in range(num_questions)]
            errors = self.core.saveExam(exam_id, question_ids, answers, self.meta['b'])

            self.assertIsNot(None, errors)



if __name__ == '__main__':
    unittest.main()
