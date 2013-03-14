from sqlalchemy import text


class ErrorReviewMixin(object):
    """ This mixin provides Error Review feature. Used in QuizDb. """
    def __init__(self):
        self.__geterrors = text(""" SELECT * FROM questions q INNER JOIN
            (SELECT question_id id FROM answers WHERE user_id=:user_id
             AND is_correct=0 LIMIT 100) e USING(id) ORDER BY RAND() LIMIT 40;
        """)
        self.__geterrors = self.__geterrors.compile(self.engine)

    def getErrorReview(self, user, lang):
        res = self.conn.execute(self.__geterrors, user_id=user)

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
        return questions

    def saveErrorReview(self, user, id_list, answers):
        t = self.conn.begin()
        try:
            self.saveQuestions(user, id_list, answers)
        except Exception:
            t.rollback()
            raise
        else:
            t.commit()
