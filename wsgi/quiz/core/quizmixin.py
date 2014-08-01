import re
from sqlalchemy import select, and_
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from .exceptions import QuizCoreError


class QuizMixin(object):
    """Mixin for working with quiz information. Used in QuizCore.

    QuizMixin provides the followin features:
        * quiz construction;
        * quiz result saving;
        * quiz statistics (not implemented yet).
    """
    def __init__(self):
        # See getQuiz() comments for more info.
        self.__rx = re.compile(".*Duplicate entry '\d+-\d+-(\d+)'")
        self.__add = "ON DUPLICATE KEY UPDATE is_correct=VALUES(is_correct)"

    # TODO: what about performance?
    # Construct query of the form:
    # SELECT * FROM (
    #   SELECT * FROM questions q WHERE quiz_type=A AND topic_id=B
    #   AND id NOT IN (C) AND id NOT IN (
    #       SELECT question_id FROM quiz_answers WHERE user_id=D
    #       AND quiz_type=q.quiz_type)
    #   LIMIT 100
    # ) t ORDER BY RAND() LIMIT 40;
    #
    # NOTE: to increase ORDER BY RAND() we use very simple trick - just
    # limit subselect before ORDER with 100 rows which ORDER BY RAND()
    # must process fast enough. If this will be slow in the future then
    # rid it off and create somethin more tricky like:
    # http://explainextended.com/2009/03/01/selecting-random-rows
    # or
    # http://hudson.su/2010/09/16/mysql-optimizaciya-order-by-rand
    # http://jan.kneschke.de/projects/mysql/order-by-rand
    #
    # NOTE: another way to filter out answered questions (with JOIN):
    #
    #   SELECT * FROM questions q LEFT JOIN quiz_answers s
    #   ON q.id=s.question_id AND s.user_id=1
    #   WHERE q.topic_id=1 and user_id is NULL;
    #
    # NOTE: if quiz answers will not be returned then current questions
    # may be appear in future quizzes.
    def __getQuery(self, quiz_type, user_id, topic_id, exclude):
        q = self.questions
        qa = self.quiz_answers

        # SELECT question_id FROM quiz_answers WHERE
        # user_id=:user_id AND quiz_type=q.quiz_type
        stmt = select([qa.c.question_id]).where(and_(
            qa.c.user_id == user_id, qa.c.quiz_type == q.c.quiz_type))

        # SELECT * FROM questions q WHERE quiz_type=:quiz_type
        # AND topic_id=:topic_id AND id NOT IN (:exclude) AND id NOT IN (...)
        # LIMIT 100
        if exclude is not None:
            not_in = [q.c.id.notin_(exclude), q.c.id.notin_(stmt)]
        else:
            not_in = [q.c.id.notin_(stmt)]

        stmt2 = select([q]).where(and_(
            q.c.quiz_type == quiz_type,
            q.c.topic_id == topic_id,
            *not_in
        )).limit(100).alias('t')

        # Final query
        stmt3 = select([stmt2]).order_by(func.rand()).limit(40)
        return stmt3

    # Get 40 random questions from for the specified topic which are
    # not answered by the specified user.
    # Answered quiz questions are placed in the quiz_answers.
    def _getQuizQuestions(self, quiz_type, user_id, topic_id, lang, exclude):
        query = self.__getQuery(quiz_type, user_id, topic_id, exclude)
        try:
            res = self.engine.execute(query)
        except SQLAlchemyError as e:
            print e
            raise QuizCoreError('Invalid parameters.')

        if lang == 'de':
            txt_lang = self.questions.c.text_de
        elif lang == 'fr':
            txt_lang = self.questions.c.text_fr
        else:
            txt_lang = self.questions.c.text

        # TODO: maybe preallocate with quiz = [None] * 40?
        quiz = []
        for row in res:
            d = {
                'id': row[self.questions.c.id],
                'text': row[txt_lang],
                'answer': row[self.questions.c.answer],
                'image': row[self.questions.c.image],
                'image_bis': row[self.questions.c.image_part]
            }

            self._aux_question_delOptionalField(d)
            quiz.append(d)
        res.close()
        return quiz

    def getQuiz(self, quiz_type, user_id, topic_id, lang, force, exclude=None):
        """Return list of Quiz questions.

        Args:
            quiz_type: Quiz type.
            user_id:   User ID for whom Quiz is generated.
            topic_id:  Topic ID from which get questions for the Quiz.
            lang:      Question language. Can be: (it, fr, de).
            force:     If all questions are answered then reset quiz state
                       and start quiz from the beginning.

        Question is represented as a dictionary with the following items:
            id        - question ID in the DB
            text      - question text
            answer    - question answer (True/False)
            image     - image ID to illustrate the question (optional)
            image_bis - image type ID (optional)
        """
        # TODO: do we need to validate topic ID?
        questions = self._getQuizQuestions(quiz_type, user_id, topic_id,
                                           lang, exclude)

        # FIXME: bug! it resets quizzes for all topics!
        # Seems all questions are answered so we make all questions
        # unanswered and generate quiz again.
        if not questions and force:
            t = self.quiz_answers
            self.engine.execute(t.delete().where(and_(
                t.c.quiz_type == quiz_type,
                t.c.user_id == user_id)))
            questions = self._getQuizQuestions(quiz_type, user_id, topic_id,
                                               lang, exclude)

        t = self.topics
        if lang == 'de':
            col = t.c.text_de
        elif lang == 'fr':
            col = t.c.text_fr
        else:
            col = t.c.text
        s = select([col], t.c.id == topic_id)
        row = self.engine.execute(s).fetchone()
        return {'topic': topic_id, 'questions': questions, 'title': row[col]}

    def saveQuiz(self, quiz_type, user_id, topic_id, questions, answers):
        """Save quiz answers for the user.

        Args:
            quiz_type:  Quiz type.
            user_id:    ID of the user for whom need to save the quiz.
            questions:  List of the quesions IDs.
            answers:    List of questions' answers.

        Raises:
            QuizCoreError

        .. note::
           questions and answers must have tha same length.
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
