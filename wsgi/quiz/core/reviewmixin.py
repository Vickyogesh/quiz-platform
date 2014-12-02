from sqlalchemy import select, and_
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from .exceptions import QuizCoreError


class ErrorReviewMixin(object):
    """This mixin provides Error Review feature. Used in QuizCore."""
    def __init__(self):
        self.__add = "ON DUPLICATE KEY UPDATE is_correct=VALUES(is_correct)"

    # Construct query of the form
    # SELECT q.* FROM questions q INNER JOIN (
    #   SELECT question_id id, quiz_type FROM answers WHERE
    #   quiz_type=A AND user_id=B AND is_correct=0 AND id NOT IN (C) LIMIT 100
    # ) e ON q.quiz_type=e.quiz_type AND q.id=e.id ORDER BY RAND() LIMIT 40
    def __getQuery(self, quiz_type, user, exclude):
        q = self.questions
        a = self.answers

        and_lst = [a.c.quiz_type == quiz_type, a.c.user_id == user,
                   a.c.is_correct == 0]
        if exclude is not None:
            and_lst.append(a.c.question_id.notin_(exclude))

        stmt = select([a.c.question_id, a.c.quiz_type]).where(
            and_(*and_lst)).limit(100).alias('e')

        stmt1 = select([q]).select_from(
            q.join(stmt, and_(q.c.quiz_type == stmt.c.quiz_type,
                   q.c.id == stmt.c.question_id))
        ).order_by(func.rand()).limit(40)
        return stmt1

    def getErrorReview(self, quiz_type, user, lang, exclude=None):
        """Get user's error review."""
        query = self.__getQuery(quiz_type, user, exclude)
        try:
            res = self.engine.execute(query)
        except SQLAlchemyError as e:
            print e
            raise QuizCoreError('Invalid parameters.')

        if lang == 'de':
            lang = self.questions.c.text_de
        elif lang == 'fr':
            lang = self.questions.c.text_fr
        else:
            lang = self.questions.c.text

        # TODO: maybe preallocate with questions = [None] * 40?
        questions = []
        for row in res:
            d = {
                'id': row[self.questions.c.id],
                'text': row[lang],
                'answer': row[self.questions.c.answer],
                'image': row[self.questions.c.image],
                'image_bis': row[self.questions.c.image_part]
            }
            self._aux_question_delOptionalField(d)
            questions.append(d)
        return {'questions': questions}

    def saveErrorReview(self, quiz_type, user, questions, answers):
        """Save user's error review."""
        questions, answers = self._aux_prepareLists(questions, answers)

        # select and check answers
        q = self.questions
        s = select([q.c.id, q.c.answer], and_(
                   q.c.quiz_type == quiz_type,
                   q.c.id.in_(questions)))
        res = self.engine.execute(s)

        ans = []
        for row, answer in zip(res, answers):
            ans.append({
                'user_id': user,
                'quiz_type': quiz_type,
                'question_id': row[q.c.id],
                'is_correct': row[q.c.answer] == answer
            })
        if ans:
            with self.engine.begin() as conn:
                t = self.answers
                conn.execute(t.insert(append_string=self.__add), ans)
