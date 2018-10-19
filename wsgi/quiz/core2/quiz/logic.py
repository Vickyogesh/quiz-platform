import re
import uuid
from sqlalchemy import select, and_
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ...core.exceptions import QuizCoreError

from ..models import db, Question, QuizAnswer, Blacklist, Topic, Chapter
from  ..meta import meta
from .ai import getAiQuestion


class QuizCore(object):

    def __init__(self):
        self.meta = meta
        self.__rx = re.compile(".*Duplicate entry '\d+-\d+-(\d+)'")

    def __getQuery(self, quiz_type, user_id, topic_id, exclude):

        prev_answers = db.session.query(QuizAnswer.question_id)\
            .filter(QuizAnswer.user_id==user_id)\
            .filter(QuizAnswer.quiz_type==quiz_type)

        query = Question.query.filter_by(quiz_type=quiz_type, topic_id=topic_id)\
            .filter(~Question.id.in_(prev_answers))\

        if exclude is not None:
            query = query.filter(~Question.id.in_(set(exclude)))

        blacklist = db.session.query(Blacklist.id).filter(Blacklist.quiz_type==quiz_type)

        query = query.filter(~Question.id.in_(blacklist)).order_by(func.random()).limit(40)

        return query

    # Question data structure
    def __question_data(self, row):
        d = {
            'id': row.id,
            'text': row.text,
            'answer': row.answer,
            'explanation': row.explanation,
            'topic_id': row.topic_id,
            'image': row.image,
            'image_bis': row.image_part
        }

        return d

    def _multi_topic_quiz(self, quiz_type, user_id, topic_id, lang, exclude, topic_lst):
        QUIZ_LEN = 40

        # querying questions for each topic and saving to dict:
        # topic_id : [question list], another_topic: [question list], ...
        topic_questions = {}
        for topic in topic_lst:
            query = self.__getQuery(quiz_type, user_id, topic, exclude)

            topic_questions[topic] = []
            for row in query:
                topic_questions[topic].append(self.__question_data(row))

        # Manual sorting for quiz questions
        # 40 question one by one from all the topics
        sorted_quiz = []

        questions_added = 0
        for question_index in range(QUIZ_LEN):
            for topic in topic_questions:
                try:
                    sorted_quiz.append(topic_questions[topic][question_index])
                    questions_added += 1
                    if questions_added == QUIZ_LEN:
                        return sorted_quiz
                except:
                    pass

        return sorted_quiz

    # Get 40 random questions from for the specified topic which are
    # not answered by the specified user.
    # Answered quiz questions are placed in the quiz_answers.
    def _getQuizQuestions(self, quiz_type, user_id, topic_id, lang, exclude, topic_lst=None):

        # Multi topic quiz
        if topic_lst is not None:
            return self._multi_topic_quiz(quiz_type, user_id, topic_id, lang, exclude, topic_lst)

        res = self.__getQuery(quiz_type, user_id, topic_id, exclude)


        # TODO: maybe preallocate with quiz = [None] * 40?
        quiz = []
        for row in res:
            quiz.append(self.__question_data(row))
        return quiz

    def getQuiz(self, quiz_type, user_id, topic_id, lang, force, exclude=None, topic_lst=None):
        """Return list of Quiz questions.

        Args:
            quiz_type: Quiz type.
            user_id:   User ID for whom Quiz is generated.
            topic_id:  Topic ID from which get questions for the Quiz.
            lang:      Question language. Can be: (it, fr, de).
            force:     If all questions are answered then reset quiz state
                       and start quiz from the beginning.

        Question is represented as a dictionary with the following items:

            * id        - question ID in the DB
            * text      - question text
            * answer    - question answer (True/False)
            * image     - image ID to illustrate the question (optional)
            * image_bis - image type ID (optional)
        """
        # TODO: do we need to validate topic ID?
        questions = self._getQuizQuestions(quiz_type, user_id, topic_id,
                                           lang, exclude, topic_lst=topic_lst)

        # FIXME: bug! it resets quizzes for all topics!
        # Seems all questions are answered so we make all questions
        # unanswered and generate quiz again.
        if not questions and force:
            QuizAnswer.query.filter_by(quiz_type=quiz_type, user_id=user_id).delete()
            db.session.commit()
            questions = self._getQuizQuestions(quiz_type, user_id, topic_id,
                                               lang, exclude, topic_lst=topic_lst)

        t = Topic.query.filter_by(id=topic_id, quiz_type=quiz_type).first()

        return {'topic': topic_id, 'questions': questions, 'title': t.text if t else ''}

    def get_ai_quiz(self, quiz_type, user_id, topic_id, lang, force, exclude=None, topic_lst=None):
        res = Topic.query.filter_by(quiz_type=quiz_type, id=topic_id).first()
        title, chapter = res.text, res.chapter_id
        session_id = uuid.uuid4().hex
        num_ex = 40
        first_question = getAiQuestion({
            "quiz_type": quiz_type,
            "chapter_id": chapter,
            "topic_id": topic_id,
            "num_ex": num_ex,
            "quiz_session": session_id,
            "u_id": user_id
        })
        return {'topic': topic_id,
                'questions': [first_question] if first_question.get('id') else [],
                'title': title,
                'session_id': session_id, 'num_ex': num_ex, 'chapter': chapter,
                "quiz_type": quiz_type}

    def getQuizByImage(self, image):
        query = Question.query.filter_by(image=image)
        questions = []
        for row in query:
            questions.append(self.__question_data(row))
        return {'image': image, 'questions': questions}

    def saveQuiz(self, quiz_type, user_id, topic_id, questions, answers):
        """Save quiz answers for the user.

        Args:
            quiz_type:  Quiz type.
            user_id:    ID of the user for whom need to save the quiz.
            questions:  List of the questions IDs.
            answers:    List of questions' answers.

        Raises:
            QuizCoreError: Already answered.

        .. note::
           Questions and answers must have tha same length.
        """
        questions, answers = self._aux_prepareLists(questions, answers)

        # select and check answers
        q = self.questions
        s = select([q.c.id, q.c.answer], and_(
                   q.c.quiz_type == quiz_type, q.c.id.in_(questions)))
        res = self.engine.execute(s)

        ans = []
        for row, answer in zip(res, answers):
            ans.append({
                'user_id': user_id,
                'quiz_type': quiz_type,
                'question_id': row[q.c.id],
                'is_correct': row[q.c.answer] == answer
            })

        if ans:
            try:
                self.engine.execute(self.quiz_answers.insert(), ans)
            except IntegrityError as e:
                g = self.__rx.match(e.message)
                if g and g.group(1):
                    raise QuizCoreError('Already answered: %s.' % g.group(1))
                else:
                    raise QuizCoreError('Already answered.')
