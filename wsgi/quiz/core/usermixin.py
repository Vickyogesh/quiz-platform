from sqlalchemy import select, text, bindparam, and_
from sqlalchemy.exc import SQLAlchemyError
from .exceptions import QuizCoreError


class UserMixin(object):
    """Mixin for working with user information. Used in QuizCore."""
    def __init__(self):
        self.__appid = self.sql("""SELECT id FROM applications
                                WHERE appkey=:appkey""")

        self.__user_by_id = self.sql("SELECT * FROM users WHERE id=:id LIMIT 1")

        self.__topicstat = self.sql("""SELECT
            t.id, t.text, t.text_fr, t.text_de,
            IFNULL((SELECT err_count/count*100 FROM topic_err_current WHERE
                user_id=:user_id AND quiz_type=t.quiz_type AND
                topic_id=t.id), -1) current,
            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND quiz_type=t.quiz_type AND
               topic_id = t.id AND
               now_date BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 7 DAY
               AND DATE(UTC_TIMESTAMP()) - INTERVAL 1 DAY
               GROUP BY topic_id), -1) week,
            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND quiz_type=t.quiz_type AND
               topic_id = t.id AND
               now_date BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 29 DAY
               AND DATE(UTC_TIMESTAMP()) - INTERVAL 8 DAY
               GROUP BY topic_id), -1) week3
            from topics t WHERE quiz_type=:quiz_type""")

        # NOTE: we skip 'in-progress' exams.
        self.__examstat = self.sql("""SELECT
        (SELECT SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100 e
         FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type)current,
        (SELECT SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100 e
         FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type AND
         start_time BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 7 DAY
         AND DATE(UTC_TIMESTAMP()) - INTERVAL 1 DAY) week,
        (SELECT SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100 e
         FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type AND
         start_time BETWEEN DATE(UTC_TIMESTAMP()) - interval 29 day
         AND DATE(UTC_TIMESTAMP()) - INTERVAL 8 DAY) week3;
        """)

        self.__examlist = self.sql("""SELECT
            exams.*, UTC_TIMESTAMP() > start_time + INTERVAL 3 HOUR
            FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type""")

        self.__topicerr = self.sql("""SELECT * FROM
            (SELECT * FROM questions WHERE topic_id=:topic_id AND
            quiz_type=:quiz_type AND id IN
            (SELECT question_id FROM answers WHERE user_id=:user_id AND
            is_correct=0 AND quiz_type=:quiz_type)) t""")

        self.__lastvisit = self.sql("""INSERT
            INTO users (id, type, quiz_type, school_id, last_visit)
            VALUES(:user_id, :type, :quiz_type, :school_id, UTC_TIMESTAMP())
            ON DUPLICATE KEY UPDATE last_visit=VALUES(last_visit)""")

    def updateUserLastVisit(self, quiz_type, user_id, type, school_id):
        self.engine.execute(self.__lastvisit, quiz_type=quiz_type,
                            user_id=user_id, type=type, school_id=school_id)

    def getAppId(self, appkey):
        try:
            row = self.__appid.execute(appkey=appkey).fetchone()
        except SQLAlchemyError:
            row = None
        if row is None:
            raise QuizCoreError('Unknown application ID.')
        return row[0]

    # NOTE: we don't use quiz_type here since even for multiple rows
    # id, type and school id will be the same.
    def _getStudentById(self, user_id):
        try:
            row = self.__user_by_id.execute(id=user_id).fetchone()
        except SQLAlchemyError:
            row = None
        if row is None:
            raise QuizCoreError('Unknown student.')
        return {'id': row[0], 'type': row[1], 'school_id': row[3]}

    def _normErr(self, err):
        if err is None:
            return -1
        elif 0 < err < 1:
            return 1
        elif 99 < err < 100:
            return 99
        return round(err)

    def _getTopicsStat(self, quiz_type, user, lang):
        if lang == 'de':
            lang = 3
        elif lang == 'fr':
            lang = 2
        else:
            lang = 1

        # TODO: maybe preallocate with stat = [None] * x?
        stat = []
        rows = self.__topicstat.execute(user_id=user, quiz_type=quiz_type)
        for row in rows:
            stat.append({
                'id': row[0],
                'text': row[lang],
                'errors': {
                    'current': self._normErr(row[4]),
                    'week': self._normErr(row[5]),
                    'week3': self._normErr(row[6])
                }
            })
        return stat

    def __getExamStat(self, quiz_type, user_id):
        try:
            row = self.__examstat.execute(user_id=user_id, quiz_type=quiz_type)
            row = row.fetchone()
        except Exception:
            row = (-1, -1, -1)
        return {
            'current': self._normErr(row[0]),
            'week': self._normErr(row[1]),
            'week3': self._normErr(row[2])
        }
        # stat = []
        # for row in rows:
        #     end = row[2]
        #     expired = row[3]
        #     if end:
        #         stat.append({'id': row[0], 'status': row[1]})
        #     elif expired:
        #         stat.append({'id': row[0], 'status': 'expired'})
        #     else:
        #         stat.append({'id': row[0], 'status': 'in-progress'})
        # return stat

    def getUserStat(self, quiz_type, user_id, lang):
        user = self._getStudentById(user_id)
        topics = self._getTopicsStat(quiz_type, user_id, lang)
        return {
            'student': user,
            'exams': self.__getExamStat(quiz_type, user_id),
            'topics': topics
        }

    def _createExamInfo(self, exam_db_row):
        start = exam_db_row[3]
        end = exam_db_row[4]
        errors = exam_db_row[5]
        expired = exam_db_row[6]

        if end:
            if errors > 4:
                status = 'failed'
            else:
                status = 'passed'
        elif expired == 1:
            status = 'expired'
        else:
            status = 'in-progress'

        return {
            'id': exam_db_row[0],
            'start': str(start),
            'end': str(end),
            'errors': errors,
            'status': status
        }

    def _getExamList(self, quiz_type, user_id):
        rows = self.__examlist.execute(user_id=user_id, quiz_type=quiz_type)
        return [self._createExamInfo(row) for row in rows]

    def getExamList(self, quiz_type, user_id):
        return {
            'student': self._getStudentById(user_id),
            'exams': self._getExamList(quiz_type, user_id)
        }

    def getTopicErrors(self, quiz_type, user_id, topic_id, lang):
        student = self._getStudentById(user_id)

        rows = self.__topicerr.execute(user_id=user_id, topic_id=topic_id,
                                       quiz_type=quiz_type)

        if lang == 'de':
            txt_lang = self.questions.c.text_de
        elif lang == 'fr':
            txt_lang = self.questions.c.text_fr
        else:
            txt_lang = self.questions.c.text

        # TODO: maybe preallocate with quiz = [None] * 40?
        questions = []
        for row in rows:
            d = {
                'id': row[self.questions.c.id],
                'text': row[txt_lang],
                'answer': row[self.questions.c.answer],
                'image': row[self.questions.c.image],
                'image_bis': row[self.questions.c.image_part]
            }

            self._aux_question_delOptionalField(d)
            questions.append(d)
        return {'student': student, 'questions': questions}
