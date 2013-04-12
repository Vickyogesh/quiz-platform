import random
from datetime import datetime
from sqlalchemy import select, func
#from profilestats import profile
from .exceptions import QuizCoreError


class ExamMixin(object):
    """Mixin for working with exams. Used in QuizCore."""
    def __init__(self):
        # Get chapters info: priority and chapter's questions' id range.
        sql = self.sql("SELECT priority, min_id, max_id FROM chapters")
        self.__stmt_ch_info = sql

        self.__create_exam = self.sql(self.exams.insert().values(
                                      start_time=func.utc_timestamp(),
                                      user_id=0))

        self.__expires = self.sql("""SELECT
            start_time + INTERVAL 3 HOUR, end_time
            FROM exams WHERE id=:exam_id""")

        self.__getexam = self.sql("""SELECT exams.*,
            UTC_TIMESTAMP() > start_time + INTERVAL 3 HOUR
            FROM exams WHERE id=:exam_id""")

        self.__set_questions = self.sql(self.exam_answers.insert().values(
                                        exam_id=0,
                                        question_id=0))

        self.__upd = self.sql("""INSERT INTO exam_answers
            (exam_id, question_id, is_correct)
            VALUES(:exam_id, :question_id, :is_correct)
            ON DUPLICATE KEY UPDATE is_correct = VALUES(is_correct)""")

        self.__examquest = self.sql("""SELECT q.*, e.is_correct FROM
            (SELECT * FROM exam_answers where exam_id=:exam_id ORDER BY add_id) e
            LEFT JOIN questions q ON e.question_id=q.id;""")

        self.__examids = self.sql("""SELECT
            question_id FROM exam_answers WHERE exam_id=:exam_id""")

        self.__updexaminfo = self.sql("""UPDATE
            exams SET end_time=UTC_TIMESTAMP(), err_count=:errors
            WHERE id=:exam_id""")

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
    # [1 - 100] and for row 2 we need select two (random) questions
    # in the range [101 - 200].
    def __generate_idList(self):
        # id_list = []
        # res = self.__stmt_ch_info.execute()
        # for row in res:
        #     # priority = row[0], min_id = row[1], max_id = row[2]
        #     id_list.extend(random.sample(xrange(row[1], row[2] + 1), row[0]))
        # return id_list
        id_norm = []
        id_high = []
        ids = None
        res = self.__stmt_ch_info.execute()
        for row in res:
            # priority = row[0], min_id = row[1], max_id = row[2]
            ids = random.sample(xrange(row[1], row[2] + 1), row[0])
            if len(ids) > 1:
                id_norm.append(ids[0])
                id_high.extend(ids[1:])
            else:
                id_norm.extend(ids)
        return id_norm, id_high

    #@profile
    def __initExam(self, user_id, questions):
        res = self.__create_exam.execute(user_id=user_id)
        exam_id = res.inserted_primary_key[0]

        vals = [{'exam_id': exam_id, 'question_id': q} for q in questions]
        self.__set_questions.execute(vals)
        return exam_id

    # Return expiration date and exam end time (if set).
    def __getExpirationDate(self, exam_id):
        row = self.__expires.execute(exam_id=exam_id).fetchone()
        if row is None:
            raise QuizCoreError('Invalid exam ID.')
        return row[0], row[1]

    def __getQuestions(self, questions, lang, dest):
        q = self.questions

        if lang == 'de':
            txt_lang = q.c.text_de
        elif lang == 'fr':
            txt_lang = q.c.text_fr
        else:
            txt_lang = q.c.text

        s = select([q], q.c.id.in_(questions))
        res = self.engine.execute(s)

        # TODO: maybe preallocate with exam = [None] * 40?
        for row in res:
            d = {
                'id': row[q.c.id],
                'text': row[txt_lang],
                'answer': row[q.c.answer],
                'image': row[q.c.image],
                'image_bis': row[q.c.image_part]
            }
            self._aux_question_delOptionalField(d)
            dest.append(d)

    def createExam(self, user_id, lang):
        norm, high = self.__generate_idList()
        exam_id = self.__initExam(user_id, norm + high)

        questions = []
        self.__getQuestions(norm, lang, questions)
        self.__getQuestions(high, lang, questions)

        # YYYY-MM-DDTHH:MM:SS
        expires, _ = self.__getExpirationDate(exam_id)
        expires = str(expires)
        exam = {'id': exam_id, 'expires': expires}
        return {'exam': exam, 'questions': questions}

    #@profile
    def saveExam(self, exam_id, questions, answers):
        expires, end_time = self.__getExpirationDate(exam_id)
        now = datetime.utcnow()

        if end_time:
            raise QuizCoreError('Exam is already passed.')
        elif now > expires:
            raise QuizCoreError('Exam is expired.')
        elif not isinstance(answers, list):
            raise QuizCoreError('Invalid value.')
        elif len(answers) != 40:
            raise QuizCoreError('Wrong number of answers.')

        res = self.__examids.execute(exam_id=exam_id)
        exam_questons = [row[0] for row in res]
        questions, answers = self._aux_prepareLists(questions, answers)

        q = self.questions
        s = select([q.c.id, q.c.answer], q.c.id.in_(exam_questons))
        res = self.engine.execute(s)

        ans = []
        wrong = 0
        for row, answer, qq, eq in zip(res, answers, questions, exam_questons):
            if qq != eq:
                raise QuizCoreError('Invalid question ID.')

            is_correct = row[q.c.answer] == answer
            if not is_correct:
                wrong += 1
            ans.append({
                'exam_id': exam_id,
                'question_id': row[q.c.id],
                'is_correct': is_correct
            })
        with self.engine.begin() as conn:
            conn.execute(self.__upd, ans)
            conn.execute(self.__updexaminfo, exam_id=exam_id, errors=wrong)

    def getExamInfo(self, exam_id, lang):
        res = self.__getexam.execute(exam_id=exam_id).fetchone()

        if res is None:
            raise QuizCoreError('Invalid exam ID.')

        user_id = res[1]
        exam = self._createExamInfo(res)
        student = self._getStudentById(user_id)
        res = self.__examquest.execute(exam_id=exam_id)

        if lang == 'de':
            txt_lang = 3
        elif lang == 'fr':
            txt_lang = 2
        else:
            txt_lang = 1

        questions = []
        for row in res:
            d = {
                'id': row[0],
                'text': row[txt_lang],
                'answer': row[4],
                'image': row[5],
                'image_bis': row[6],
                'is_correct': row[9]
            }
            self._aux_question_delOptionalField(d)
            questions.append(d)

        return {'exam': exam, 'student': student, 'questions': questions}
