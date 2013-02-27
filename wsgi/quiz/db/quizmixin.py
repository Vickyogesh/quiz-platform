from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from ..exceptions import QuizCoreError


# See QuizCore docs for more info
class QuizMixin(object):
    """ Mixin for working with quiz information. Used in QuizDb.

    QuizMixin provides the followin features:
        * quiz construction;
        * quiz result saving;
        * quiz statistics (not implemented yet).
    """
    def __init__(self):
        # See getQuiz() comments for more info.
        self.__getquiz = text(
            """SELECT * FROM (SELECT * FROM questions WHERE id NOT IN (
            SELECT question_id FROM quiz_stat WHERE user_id=:user_id)
            AND topic_id=:topic_id LIMIT 100) t ORDER BY RAND() LIMIT 40;""")
        self.__getquiz = self.__getquiz.compile(self.engine)

    # Get 40 random questions from for the specified topic which are
    # not answered by the specified user.
    #
    # Query parts:
    # * how to get already answered quetions:
    #
    #       SELECT question_id FROM quiz_stat WHERE user_id=1;
    #
    # * how to filter out answered questions for the topic:
    #
    #       SELECT * FROM questions WHERE topic_id=1 AND
    #       id NOT IN (SELECT question_id FROM quiz_stat WHERE user_id=1);
    #
    # Result query:
    #
    #   SELECT * FROM (SELECT * FROM questions WHERE id NOT IN (
    #       SELECT question_id FROM quiz_stat WHERE user_id=1)
    #   AND topic_id=1 LIMIT 100) t ORDER BY RAND() LIMIT 40;
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
    #   SELECT * FROM questions q LEFT JOIN quiz_stat s
    #   ON q.id=s.question_id and s.user_id=1
    #   WHERE q.topic_id=1 and user_id is NULL;
    #
    def getQuiz(self, topic_id, user_id, lang):
        res = self.conn.execute(self.__getquiz,
                                topic_id=topic_id, user_id=user_id)
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
        return quiz

    def saveQuizResult(self, user_id, questions, answers):
        if len(questions) != len(answers):
            raise QuizCoreError('Parameters length mismatch.')

        # questions must contain integer values since it represents
        # list of IDs. It's important to have valid list
        # because select will skip bad values and answers
        # will not correspond to rows.
        #
        # Since sqlalchemy in_() accept iterable object
        # we may use generator here.
        questions = (int(x) for x in questions)
        answers = (int(x) for x in answers)

        # TODO: seems not very optimal way since it creates many list objects.
        #
        # We need sorted list of answers to correctly compare in the
        # 'for row, answer in zip(res, answers)' later, since db server
        # will return sorted list of questions' IDs.
        # See also test_saveQuizUnordered() test in the tests/test_db_quiz.py
        try:
            lst = list(sorted(zip(questions, answers), key=lambda pair: pair[0]))
            questions, answers = zip(*lst)
        except ValueError:
            raise QuizCoreError('Invalid value.')

        q = self.questions
        s = select([q.c.id, q.c.answer], q.c.id.in_(questions))
        res = self.conn.execute(s)

        if res:
            stat = []
            for row, answer in zip(res, answers):
                if row[q.c.answer] == answer:
                    stat.append({'user_id': user_id,
                                'question_id': row[q.c.id]})

        if stat:
            try:
                self.conn.execute(self.quiz_stat.insert(), stat)
            except IntegrityError as e:
                # seems quiz_stat already contains value from the answers
                print(e)
                raise QuizCoreError('Contains already answered questions.')
