import random
import datetime as dt
from sqlalchemy import select, func, and_
from ..models import db, Chapter, Exam, ExamAnswer, Question, Blacklist
from flask import g, url_for
from ...core.exceptions import QuizCoreError


def _aux_prepareLists(questions, answers):
    try:
        if len(questions) != len(answers):
            raise QuizCoreError('Parameters length mismatch.')
        elif not answers:
            raise QuizCoreError('Empty list.')
    except QuizCoreError:
        raise
    except Exception:
        raise QuizCoreError('Invalid value.')


    questions = (int(x) for x in questions)
    answers = (int(x) for x in answers)

    try:
        lst = list(sorted(zip(questions, answers), key=lambda pair: pair[0]))
        questions, answers = zip(*lst)
    except ValueError:
        raise QuizCoreError('Invalid value.')
    return questions, answers


class ExamCore(object):
    def __init__(self, meta):
        self.meta = meta


    # Create list of exam questions.
    # quiz_type is defined above in the exam_meta.
    # 1 - b2011
    # 2 - cqc
    # 4 - scooter
    # 5 - 11 - truck
    # 60 - 66 - revisioni
    def __generate_idList(self, quiz_type, examType):
        if quiz_type == 2:
            return self.__generate_idListCQC(quiz_type, examType)
        elif quiz_type == 4:
            return self.__generate_idListScooter(quiz_type, examType)
        elif quiz_type in (1, 3, 50):
            return self.__generate_idListB(quiz_type, examType)
        elif 5 <= quiz_type <= 11:
            return self.__generate_idListTruck(quiz_type, examType)
        elif 60 <= quiz_type <= 66:
            return self.__generate_idListRev(quiz_type, examType)
        else:
            raise QuizCoreError('Unknown exam generator')

    def __get_blacklisted_ids(self, quiz_type):
        return [x.id for x in Blacklist.query.filter(Blacklist.quiz_type == quiz_type)]

    def __filter_questions(self, min, max, blacklist):
        return [x for x in xrange(min, max + 1) if x not in blacklist]

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
        # Get blacklisted IDs.
        blacklist = self.__get_blacklisted_ids(quiz_type)

        id_norm = []
        id_high = []
        ids = None

        res = Chapter.query.filter_by(quiz_type=quiz_type)
        for row in res:
            # Build ID list with excluding blacklisted ones.
            allowed_ids = self.__filter_questions(row.min_id, row.max_id, blacklist)

            # priority = row[0], min_id = row[1], max_id = row[2]
            # ids = random.sample(xrange(row[1], row[2] + 1), row[0])
            ids = random.sample(allowed_ids, row.priority)
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
            start = 14
            end = 16
        elif examType == 'merci':
            start = 11
            end = 13
        else:
            raise QuizCoreError('Unknown exam type.')

        t = self.chapters
        sql_min = select([t.c.min_id]).where(and_(
            t.c.quiz_type == quiz_type, t.c.id == start)).as_scalar()
        sql_max = select([t.c.max_id]).where(and_(
            t.c.quiz_type == quiz_type, t.c.id == end)).as_scalar()
        sql = select([sql_min, sql_max])

        res = self.engine.execute(sql).fetchone()
        num_questions = g.quiz_meta['exam_meta']['num_questions']

        blacklist = self.__get_blacklisted_ids(quiz_type)
        allowed_ids = self.__filter_questions(res[0], res[1], blacklist)

        return random.sample(allowed_ids, num_questions), []

    # Create list of exam questions for CQC quiz
    # 3 questions per topic. Total 30 questions.
    def __generate_idListScooter(self, quiz_type, examType):
        blacklist = self.__get_blacklisted_ids(quiz_type)
        id_list = []

        t = self.chapters
        res = self.__stmt_ch_info.execute(quiz_type=quiz_type)
        for row in res:
            allowed_ids = self.__filter_questions(row[1], row[2], blacklist)
            # 3 random questions for each chapter
            vals = random.sample(allowed_ids, 3)
            id_list.extend(vals)
        return id_list, []

    def __generate_idListTruck(self, quiz_type, examType):
        exam_meta = self.meta['cde']['exam_meta']
        # FIXME: bug. probably cache issue. sometimes when change cde license - it still use old quiz meta
        questions_per_chapter = exam_meta.get(quiz_type, exam_meta)['questions_per_chapter']

        res = Chapter.query.filter_by(quiz_type=quiz_type).order_by(Chapter.id)

        blacklist = self.__get_blacklisted_ids(quiz_type)
        id_list = []
        for i, row in enumerate(res):
            allowed_ids = self.__filter_questions(row.min_id,
                                                  row.max_id, blacklist)
            lst = random.sample(allowed_ids, questions_per_chapter[i])
            id_list.extend(lst)
        return id_list, []

    def __generate_idListRev(self, quiz_type, examType):
        exam_meta = g.quiz_meta['exam_meta']
        questions_per_chapter = exam_meta['questions_per_chapter']

        t = self.chapters
        sql = select([t.c.min_id, t.c.max_id]).where(t.c.quiz_type == quiz_type)
        sql = sql.order_by(t.c.id)

        blacklist = self.__get_blacklisted_ids(quiz_type)
        id_list = []
        for i, row in enumerate(self.engine.execute(sql)):
            allowed_ids = self.__filter_questions(row[t.c.min_id],
                                                  row[t.c.max_id], blacklist)
            lst = random.sample(allowed_ids, questions_per_chapter[i])
            id_list.extend(lst)
        return id_list, []

    def __initExam(self, quiz_type, user_id, questions):
        # FIXME: for some reasons sqlalchemy do not return inserted id
        # exam = Exam(quiz_type=quiz_type, user_id=user_id, start_time=func.utc_timestamp())
        # db.session.add(exam)
        # db.session.flush()
        # Temp solution:
        res = db.engine.execute("INSERT INTO exams (quiz_type, user_id, start_time) VALUES (%s, %s, %s)",
                                quiz_type, user_id, dt.datetime.utcnow())

        exam_id = res.lastrowid

        for q in questions:
            db.session.add(ExamAnswer(exam_id=exam_id, quiz_type=quiz_type, question_id=q))
        db.session.commit()
        return exam_id

    # Return expiration date, end time (if set) and quiz_type for exam.
    def __getExamInfo(self, exam_id):
        res = Exam.query.filter_by(id=exam_id).first()
        if not res:
            raise QuizCoreError('Invalid exam ID.')
        return res.start_time + dt.timedelta(hours=3), res.end_time, res.quiz_type

    def __getQuestions(self, quiz_type, questions, lang, dest):

        res = Question.query.filter_by(quiz_type=quiz_type).filter(Question.id.in_(questions))


        for row in res:
            if lang == "it": txt = row.text
            elif lang == "de": txt = row.text_de
            elif lang == 'fr': txt = row.text_fr
            else: raise QuizCoreError('Invalid language.')

            d = {
                'id': row.id,
                'text': txt,
                'answer': row.answer,
                'explanation': row.explanation,
                'image': row.image,
                'image_bis': row.image_part
            }
            dest.append(d)


    # NOTE: exam_id is always unique so we don't need to specify quiz_type
    # for the __getExamInfo()
    def createExam(self, quiz_type, user_id, lang, examType=None):
        """Create new exam.

        Args:
            quiz_type: Quiz type ID.
            user_id: ID if the user for whom create exam.
            lang: Language of the exam questions.
            examType: Exam type for the CQC quiz.

        Returns:
            Dict with exam metadata and questions.
        """
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

    def saveExam(self, exam_id, questions, answers, meta):
        """Save exam answers.

        Args:
            exam_id: Exam ID.
            questions: Exam questions list (IDs of questions).
            answers:List of answers.

        Returns:
            Number of wrong answers.

        Raises:
            QuizCoreError: Exam is already passed.
            QuizCoreError: Exam is expired.
            QuizCoreError: Invalid value.
            QuizCoreError: Wrong number of answers.
            QuizCoreError: Invalid question ID.
        """
        expires, end_time, quiz_type = self.__getExamInfo(exam_id)
        now = dt.datetime.utcnow()

        if end_time:
            raise QuizCoreError('Exam is already passed.')
        elif now > expires:
            raise QuizCoreError('Exam is expired.')
        elif not isinstance(answers, list):
            raise QuizCoreError('Invalid value.')

        meta = meta['exam_meta']
        exam_answers = meta['num_questions']

        if len(answers) != exam_answers:
            raise QuizCoreError('Wrong number of answers.')

        res = ExamAnswer.query.filter_by(exam_id=exam_id)
        exam_questions = [row.question_id for row in res]
        questions, answers = _aux_prepareLists(questions, answers)

        res = Question.query.filter_by(quiz_type=quiz_type).filter(Question.id.in_(exam_questions))

        wrong = 0
        for row, answer, qq, eq in zip(res, answers, questions, exam_questions):
            if qq != eq:
                raise QuizCoreError('Invalid question ID.')

            is_correct = row.answer == answer
            if not is_correct:
                wrong += 1

            ans = ExamAnswer.query.filter_by(exam_id=exam_id, question_id=row.id, quiz_type=quiz_type)
            ans.is_correct = is_correct


        exam = Exam.query.filter_by(id=exam_id)

        exam.end_time = dt.datetime.utcnow()
        exam.err_count = wrong

        db.session.commit()

        return wrong

    def getExamInfo(self, exam_id, lang):
        """Exam details.

        Args:
            exam_id: Exam ID.
            lang: questions language.
        """
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
                'explanation': row[q.c.explanation],
                'is_correct': row[11]
            }
            self._aux_question_delOptionalField(d)
            questions.append(d)

        return {'exam': exam, 'student': student, 'questions': questions}


def get_urls(session):
    urls = {'exam': url_for('core2.save_exam', id=0)[:-1],
            'back': '/ui/' + session['quiz_name'],
            'image': '/img/',
            'exam_review': '/ui/{}/exam_review/'.format(session['quiz_name'])}
    return urls
