import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

import unittest
from quiz.core2.models import db, QuizAnswer
from test_common import app, truncate_answers


class QuizTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        with self.app.app_context():
            from quiz.core2.quiz.logic import QuizCore
            self.core = QuizCore()
            truncate_answers(db.engine)

    def tearDown(self):
        with self.app.app_context():
            truncate_answers(db.engine)

    def test_get_single_quiz(self):
        with self.app.app_context():
            quiz = self.core.getQuiz(50, 1, 1, 'it', False)
            questions = quiz['questions']

            self.assertEqual(40, len(questions))

            question = questions[20]
            self.assertIn('id', question)
            self.assertIn('text', question)
            self.assertIn('answer', question)

            # Get quiz for the topic with with wrong id - must return empty list
            quiz = self.core.getQuiz(1, 12, 9000, 'it', False)
            self.assertEqual(0, len(quiz['questions']))

            quiz = self.core.getQuiz(999, 1, 1, 'it', False)
            self.assertEqual(0, len(quiz['questions']))

            # testing force quiz get
            # adding fake quiz answers
            for a in range(1, 500):
                db.session.add(QuizAnswer(user_id=1, quiz_type=5, question_id=a, is_correct=0))
            db.session.commit()

            quiz = self.core.getQuiz(5, 1, 1, 'it', True, exclude=range(500, 1300))

            answers = QuizAnswer.query.filter_by(user_id=1, quiz_type=5).all()

            self.assertEqual(0, len(answers))



    def test_get_multi_quiz(self):
        topic_list = [3, 12, 15, 22]
        with self.app.app_context():
            quiz = self.core.getQuiz(50, 1, 1, 'it', False, topic_lst=topic_list)
            questions = quiz['questions']

            self.assertEqual(40, len(questions))

            # checking if there different topics in questions list
            res_topics = []

            for q in questions:
                res_topics.append(q['topic_id'])
            res_topics = list(set(res_topics))

            self.assertEqual(len(topic_list), len(res_topics))


if __name__ == '__main__':
    unittest.main()
