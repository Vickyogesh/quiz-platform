import random
from datetime import datetime
from sqlalchemy import select, func, and_, between
#from profilestats import profile
from .exceptions import QuizCoreError


class ExamMixin(object):
    """Mixin for working with exams. Used in QuizCore."""
    def __init__(self):
        # Get chapters info: priority and chapter's questions' id range.
        sql = self.sql("""SELECT priority, min_id, max_id FROM chapters
            WHERE quiz_type=:quiz_type""")
        self.__stmt_ch_info = sql

        self.__create_exam = self.sql(self.exams.insert().values(
                                      quiz_type=0,
                                      start_time=func.utc_timestamp(),
                                      user_id=0))

        self.__exam_info = self.sql("""SELECT
            start_time + INTERVAL 3 HOUR, end_time, quiz_type
            FROM exams WHERE id=:exam_id""")

        self.__getexam = self.sql("""SELECT exams.*,
            UTC_TIMESTAMP() > start_time + INTERVAL 3 HOUR
            FROM exams WHERE id=:exam_id""")

        self.__set_questions = self.sql(self.exam_answers.insert().values(
                                        quiz_type=0,
                                        exam_id=0,
                                        question_id=0))

        self.__upd = self.sql("""INSERT INTO exam_answers
            (exam_id, question_id, quiz_type, is_correct)
            VALUES(:exam_id, :question_id, :quiz_type, :is_correct)
            ON DUPLICATE KEY UPDATE is_correct = VALUES(is_correct)""")

        self.__examquest = self.sql("""SELECT q.*, e.is_correct FROM
            (SELECT * FROM exam_answers where exam_id=:exam_id ORDER BY add_id) e
            LEFT JOIN questions q ON e.quiz_type=q.quiz_type AND e.question_id=q.id;""")

        self.__examids = self.sql("""SELECT
            question_id FROM exam_answers WHERE exam_id=:exam_id
            ORDER BY question_id""")

        self.__updexaminfo = self.sql("""UPDATE
            exams SET end_time=UTC_TIMESTAMP(), err_count=:errors
            WHERE id=:exam_id""")

    # Create list of exam questions.
    # quiz_type is defined in the QuizApp (quiz/wsgi.py)
    # 1 - b2011
    # 2 - cqc
    # 4 - scooter
    def __generate_idList(self, quiz_type, examType):
        if quiz_type == 2:
            return self.__generate_idListCQC(quiz_type, examType)
        elif quiz_type == 4:
            return self.__generate_idListScooter(quiz_type, examType)
        else:
            return self.__generate_idListB(quiz_type, examType)

    # Create list of exam questions for B quiz.
    # At first, we get info about chapters: chapter priority,
    # min question ID for the chapter and max question ID for the chapter.
    # Example:
    #
    # | priority | min_id  |  max_id
    # |----------+---------+---------
    # |     1    |    1    |   100
    # |     2    |   101   |   200
    #
    # This means what for row 1 we need select one question in the range
    # [1 - 100] and for row 2 we need select two (random) questions
    # in the range [101 - 200].
    def __generate_idListB(self, quiz_type, examType):
        id_norm = []
        id_high = []
        ids = None
        res = self.__stmt_ch_info.execute(quiz_type=quiz_type)
        for row in res:
            # priority = row[0], min_id = row[1], max_id = row[2]
            ids = random.sample(xrange(row[1], row[2] + 1), row[0])
            if len(ids) > 1:
                id_norm.append(ids[0])
                id_high.extend(ids[1:])
            else:
                id_norm.extend(ids)
        return id_norm, id_high

    # Create list of exam questions for CQC quiz
    # if examType = generale we use chapters 1 - 10
    # if examType = persone we use chapters 11 - 13
    # if examType = merci we use chapters 14 - 16
    # else throw exception
    def __generate_idListCQC(self, quiz_type, examType):
        if examType == 'generale':
            start = 1
            end = 10
        elif examType == 'persone':
            start = 11
            end = 13
        elif examType == 'merci':
            start = 14
            end = 16
        else:
            raise QuizCoreError('Unknown exam type.')

        t = self.chapters
        sql_min = select([t.c.min_id]).where(and_(
            t.c.quiz_type == quiz_type, t.c.id == start)).as_scalar()
        sql_max = select([t.c.max_id]).where(and_(
            t.c.quiz_type == quiz_type, t.c.id == end)).as_scalar()
        sql = select([sql_min, sql_max])

        res = self.engine.execute(sql).fetchone()
        start = res[0]
        end = res[1] + 1
        return random.sample(xrange(start, end), 60), []

    # Create list of exam questions for CQC quiz
    # 3 questions per topic. Total 30 questions.
    def __generate_idListScooter(self, quiz_type, examType):
        id_list = []

        t = self.chapters
        res = self.__stmt_ch_info.execute(quiz_type=quiz_type)
        for row in res:
            # 3 random questions for each chapter
            vals = random.sample(xrange(row[1], row[2] + 1), 3)
            id_list.extend(vals)
        return id_list, []

    #@profile
    def __initExam(self, quiz_type, user_id, questions):
        res = self.__create_exam.execute(quiz_type=quiz_type, user_id=user_id)
        exam_id = res.inserted_primary_key[0]

        vals = [{'exam_id': exam_id, 'quiz_type': quiz_type, 'question_id': q}
                for q in questions]
        self.__set_questions.execute(vals)
        return exam_id

    # Return expiration date, end time (if set) and quiz_type for exam.
    def __getExamInfo(self, exam_id):
        row = self.__exam_info.execute(exam_id=exam_id).fetchone()
        if row is None:
            raise QuizCoreError('Invalid exam ID.')
        return row[0], row[1], row[2]

    def __getQuestions(self, quiz_type, questions, lang, dest):
        q = self.questions

        s = q.select().where(and_(
            q.c.quiz_type == quiz_type, q.c.id.in_(questions)))
        s = s.order_by(func.field(q.c.id, *questions))
        res = self.engine.execute(s)

        # TODO: maybe preallocate with exam = [None] * 40?
        if lang == 'it':
            for row in res:
                d = {
                    'id': row[q.c.id],
                    'text': row[q.c.text],
                    'answer': row[q.c.answer],
                    'image': row[q.c.image],
                    'image_bis': row[q.c.image_part]
                }
                self._aux_question_delOptionalField(d)
                dest.append(d)
        else:
            if lang == 'de':
                txt_lang = q.c.text_de
            elif lang == 'fr':
                txt_lang = q.c.text_fr
            else:
                raise QuizCoreError('Invalid language.')
            for row in res:
                d = {
                    'id': row[q.c.id],
                    'text': row[q.c.text],
                    'text_extra': row[txt_lang],
                    'answer': row[q.c.answer],
                    'image': row[q.c.image],
                    'image_bis': row[q.c.image_part]
                }
                self._aux_question_delOptionalField(d)
                dest.append(d)

    # NOTE: exam_id is always unique so we don't need to specify quiz_type
    # for the __getExamInfo()
    def createExam(self, quiz_type, user_id, lang, examType=None):
        norm, high = self.__generate_idList(quiz_type, examType)
        exam_id = self.__initExam(quiz_type, user_id, norm + high)

        questions = []
        self.__getQuestions(quiz_type, norm, lang, questions)
        if high:
            self.__getQuestions(quiz_type, high, lang, questions)

        # YYYY-MM-DDTHH:MM:SS
        expires, _, _ = self.__getExamInfo(exam_id)
        expires = str(expires)
        exam = {'id': exam_id, 'expires': expires}
        return {'exam': exam, 'questions': questions}

    #@profile
    def saveExam(self, exam_id, questions, answers):
        expires, end_time, quiz_type = self.__getExamInfo(exam_id)
        now = datetime.utcnow()

        if end_time:
            raise QuizCoreError('Exam is already passed.')
        elif now > expires:
            raise QuizCoreError('Exam is expired.')
        elif not isinstance(answers, list):
            raise QuizCoreError('Invalid value.')

        if quiz_type == 2:
            exam_answers = 60
        elif quiz_type == 4:
            exam_answers = 30
        else:
            exam_answers = 40

        if len(answers) != exam_answers:
            raise QuizCoreError('Wrong number of answers.')

        res = self.__examids.execute(exam_id=exam_id)
        exam_questions = [row[0] for row in res]
        questions, answers = self._aux_prepareLists(questions, answers)

        # Get questions
        q = self.questions
        s = select([q.c.id, q.c.answer], and_(
                   q.c.quiz_type == quiz_type,
                   q.c.id.in_(exam_questions)))
        res = self.engine.execute(s)

        ans = []
        wrong = 0
        for row, answer, qq, eq in zip(res, answers, questions, exam_questions):
            if qq != eq:
                raise QuizCoreError('Invalid question ID.')

            is_correct = row[q.c.answer] == answer
            if not is_correct:
                wrong += 1
            ans.append({
                'exam_id': exam_id,
                'question_id': row[q.c.id],
                'quiz_type': quiz_type,
                'is_correct': is_correct
            })

        with self.engine.begin() as conn:
            conn.execute(self.__upd, ans)
            conn.execute(self.__updexaminfo, exam_id=exam_id, errors=wrong)
        return wrong

    def getExamInfo(self, exam_id, lang):
        res = self.__getexam.execute(exam_id=exam_id).fetchone()

        if res is None:
            raise QuizCoreError('Invalid exam ID.')

        user_id = res[self.exams.c.user_id]
        exam = self._createExamInfo(res)
        student = self._getStudentById(user_id)
        res = self.__examquest.execute(exam_id=exam_id)
        q = self.questions

        if lang == 'de':
            txt_lang = q.c.text_de
        elif lang == 'fr':
            txt_lang = q.c.text_fr
        else:
            txt_lang = q.c.text

        questions = []
        for row in res:
            d = {
                'id': row[q.c.id],
                'text': row[txt_lang],
                'answer': row[q.c.answer],
                'image': row[q.c.image],
                'image_bis': row[q.c.image_part],
                'is_correct': row[10]
            }
            self._aux_question_delOptionalField(d)
            questions.append(d)

        return {'exam': exam, 'student': student, 'questions': questions}
