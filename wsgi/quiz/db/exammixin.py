import random
from datetime import datetime
from sqlalchemy import select, text, func, bindparam, and_
from ..exceptions import QuizCoreError


class ExamMixin(object):
    """ Mixin for working with exams. Used in QuizDb. """
    def __init__(self):

        # Get chapters info: priority and chapter's questions' id range.
        query = text('SELECT priority, min_id, max_id FROM chapters')
        self.__stmt_ch_info = query.compile(self.engine)

        t = self.exams
        self.__create_exam = t.insert().values(start_time=func.utc_timestamp(),
                                               user_id=0)
        self.__create_exam = self.__create_exam.compile(self.engine)

        self.__expires = text("""SELECT start_time + interval 3 hour, end_time
                              from exams where id=:exam_id""")
        self.__expires = self.__expires.compile(self.engine)

        t = self.exams_stat
        self.__set_questions = t.insert().values(exam_id=0, question_id=0)
        self.__set_questions = self.__set_questions.compile(self.engine)

        self.__upd = t.update().values(is_correct=bindparam('is_correct'))
        self.__upd = self.__upd.where(and_(t.c.exam_id == bindparam('exam_id'),
                                      t.c.question_id == bindparam('question_id')))
        self.__upd = self.__upd.compile(self.engine)

        self.__upd_examstat = text("call update_exam_stat(:exam_id, :passed);")
        self.__upd_examstat = self.__upd_examstat.compile(self.engine)

    # Create list of exam questions.
    # At first, we get info about chapters: chapter priority,
    # min question ID for the chapter and max question ID for the chapter.
    # Example:
    #
    # | priority | min_id  |  max_id
    # |----------+-----+------
    # |     1    |    1    |  100
    # |     2    |   101   |  200
    #
    # This means what for row 1 we need select one question in the range
    # [0 - 100] and for row 2 we need select two (random) questions
    # in the range [101 - 200].
    def __generate_idList(self):
        id_list = []
        res = self.conn.execute(self.__stmt_ch_info)
        for row in res:
            min_id = row[1]
            max_id = row[2]
            delta = max_id - min_id + 1

            # Create random ID in the range [min_id - max_id]
            for i in xrange(row[0]):
                id_list.append(int(min_id + delta * random.random()))
        return id_list

    def __initExam(self, user_id, questions):
        res = self.conn.execute(self.__create_exam, user_id=user_id)
        exam_id = res.inserted_primary_key[0]

        # TODO: optimize me
        vals = []
        for q in questions:
            vals.append({'exam_id': exam_id, 'question_id': q})
        self.conn.execute(self.__set_questions, vals)
        return exam_id

    def __getExpirationDate(self, exam_id):
        row = self.conn.execute(self.__expires, exam_id=exam_id).fetchone()
        return row[0], row[1]

    def __getQuestions(self, questions, lang):
        q = self.questions

        if lang == 'de':
            txt_lang = q.c.text_de
        elif lang == 'fr':
            txt_lang = q.c.text_fr
        else:
            txt_lang = q.c.text

        s = select([q], q.c.id.in_(questions)).order_by(func.rand())
        res = self.conn.execute(s)

        # TODO: maybe preallocate with exam = [None] * 40?
        exam = []
        for row in res:
            d = {
                'id': row[q.c.id],
                'text': row[txt_lang],
                'answer': row[q.c.answer],
                'image': row[q.c.image],
                'image_bis': row[q.c.image_part]
            }
            self._aux_question_delOptionalField(d)
            exam.append(d)

        return exam

    def createExam(self, user_id, lang):
        id_list = self.__generate_idList()
        exam_id = self.__initExam(user_id, id_list)
        questions = self.__getQuestions(id_list, lang)

        # YYYY-MM-DDTHH:MM:SS
        expires, _ = self.__getExpirationDate(exam_id)
        expires = str(expires)
        return {'exam_id': exam_id, 'expires': expires, 'questions': questions}

    def saveExam(self, exam_id, questions, answers):
        expires, end_time = self.__getExpirationDate(exam_id)
        now = datetime.utcnow()

        if end_time:
            raise QuizCoreError('Exam is already passed.')
        if now > expires:
            raise QuizCoreError('Exam is expired.')
        elif len(answers) != 40:
            raise QuizCoreError('Wrong number of answers.')

        questions, answers = self._aux_prepareLists(questions, answers)

        q = self.questions
        s = select([q.c.id, q.c.answer], q.c.id.in_(questions))
        res = self.conn.execute(s)

        t = self.conn.begin()
        try:
            wrong = 0
            for row, answer in zip(res, answers):
                qid = row[q.c.id]
                is_correct = row[q.c.answer] == answer
                if not is_correct:
                    wrong += 1
                self.conn.execute(self.__upd, is_correct=is_correct,
                                  exam_id=exam_id, question_id=qid)
                self.conn.execute(self.__upd_examstat, exam_id=exam_id,
                                  passed=wrong < 4)
        except Exception:
            t.rollback()
            raise
        else:
            t.commit()
