from sqlalchemy import select, text
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
            """SELECT * FROM (SELECT * FROM questions WHERE topic_id=:topic_id
            AND id NOT IN (SELECT question_id FROM answers WHERE
            user_id=:user_id AND is_correct=1) LIMIT 100) t
            ORDER BY RAND() LIMIT 40;""")

        self.__getquiz = self.__getquiz.compile(self.engine)

        self.__add = "ON DUPLICATE KEY UPDATE is_correct=VALUES(is_correct)"

    # Get 40 random questions from for the specified topic which are
    # not answered by the specified user.
    #
    # Query parts:
    # * how to get correctly answered quetions:
    #
    #       SELECT question_id FROM answers WHERE user_id=1 AND is_correct=1;
    #
    # * how to filter out answered questions for the topic:
    #
    #       SELECT * FROM questions WHERE topic_id=1 AND
    #       id NOT IN (SELECT question_id FROM answers WHERE
    #       user_id=1 AND is_correct=1);
    #
    # Result query:
    #
    #   SELECT * FROM (SELECT * FROM questions WHERE topic_id=1
    #   AND id NOT IN (SELECT question_id FROM answers WHERE
    #   user_id=1 AND is_correct=1) LIMIT 100) t ORDER BY RAND() LIMIT 40;
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
    #   SELECT * FROM questions q LEFT JOIN answers s
    #   ON q.id=s.question_id AND s.user_id=1 AND s.is_correct=1
    #   WHERE q.topic_id=1 and user_id is NULL;
    #
    def getQuiz(self, topic_id, user_id, lang):
        res = self.__getquiz.execute(topic_id=topic_id, user_id=user_id)
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

        # TODO: we need to validate topic ID and also
        # put answered questions if there are not enough unanswered
        # questions for the quiz.
        return quiz

        # if not quiz:
        #     raise QuizCoreError('Invalid topic ID.')
        # else:
        #     return quiz

    def saveQuestions(self, user_id, questions, answers):
        # TODO: maybe check len(ans) == len(questions) ?
        questions, answers = self._aux_prepareLists(questions, answers)

        # select and check answers
        q = self.questions
        s = select([q.c.id, q.c.answer], q.c.id.in_(questions))
        res = self.engine.execute(s)

        ans = []
        for row, answer in zip(res, answers):
            ans.append({
                'user_id': user_id,
                'question_id': row[q.c.id],
                'is_correct': row[q.c.answer] == answer
            })

        if ans:
            with self.engine.begin() as conn:
                conn.execute(self.answers.insert(
                             append_string=self.__add), ans)

    def saveQuizResult(self, user_id, topic_id, questions, answers):
        self.saveQuestions(user_id, questions, answers)
