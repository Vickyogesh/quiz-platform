from sqlalchemy import text, select, and_


class ErrorReviewMixin(object):
    """This mixin provides Error Review feature. Used in QuizCore."""
    def __init__(self):
        self.__geterrors = text(""" SELECT * FROM questions q INNER JOIN
            (SELECT question_id id FROM answers WHERE user_id=:user_id
             AND is_correct=0 LIMIT 100) e USING(id) ORDER BY RAND() LIMIT 40;
        """)
        self.__geterrors = self.__geterrors.compile(self.engine)
        self.__add = "ON DUPLICATE KEY UPDATE is_correct=VALUES(is_correct)"

    def getErrorReview(self, user, lang):
        res = self.__geterrors.execute(user_id=user)

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

    def saveErrorReview(self, user, questions, answers):
        questions, answers = self._aux_prepareLists(questions, answers)

        # select and check answers
        q = self.questions
        s = select([q.c.id, q.c.answer], q.c.id.in_(questions))
        res = self.engine.execute(s)

        ans = []
        for row, answer in zip(res, answers):
            ans.append({
                'user_id': user,
                'question_id': row[q.c.id],
                'is_correct': row[q.c.answer] == answer
            })
        # ans = [row[q.c.id] for row, answer in zip(res, answers)
        #        if row[q.c.answer] == answer]
        # ans = []
        # for row, answer in zip(res, answers):
        #     if row[q.c.answer] == answer:
        #         ans.append(row[q.c.id])
        if ans:
            with self.engine.begin() as conn:
                t = self.answers
                conn.execute(t.insert(append_string=self.__add), ans)
                # d = t.delete().where(and_(t.c.user_id == user,
                #                      t.c.question_id.in_(ans)))
                # conn.execute(d)
