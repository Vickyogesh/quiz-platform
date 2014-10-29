from sqlalchemy.exc import SQLAlchemyError
from .exceptions import QuizCoreError
from .exammixin import exam_meta


class UserMixin(object):
    """Mixin for working with user information. Used in QuizCore."""
    def __init__(self):
        self.__appid = self.sql("""SELECT id FROM applications
                                WHERE appkey=:appkey""")

        self.__user_by_id = \
            self.sql("SELECT * FROM users WHERE id=:id LIMIT 1")

        self.__topicstat = self.sql("""SELECT
            t.id, t.text, t.text_fr, t.text_de,
            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND quiz_type=t.quiz_type AND topic_id = t.id
               AND DATE(now_date) = DATE(UTC_TIMESTAMP())
               GROUP BY topic_id), -1) current,

            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND quiz_type=t.quiz_type AND topic_id = t.id
               AND
               DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)
               AND DATE(UTC_TIMESTAMP() - INTERVAL 1 DAY)
               GROUP BY topic_id), -1) week,

            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND quiz_type=t.quiz_type AND topic_id = t.id
               AND
               DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 62 DAY)
               AND DATE(UTC_TIMESTAMP() - INTERVAL 8 DAY)
               GROUP BY topic_id), -1) week3
            from topics t WHERE quiz_type=:quiz_type order by t.id""")

        # NOTE: we skip 'in-progress' exams.
        self.__examstat = self.sql("""SELECT
        (SELECT SUM(IF(err_count > :numerr, 1, 0))/COUNT(end_time)*100 e
         FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type AND
         DATE(start_time) = DATE(UTC_TIMESTAMP())) current,

        (SELECT SUM(IF(err_count > :numerr, 1, 0))/COUNT(end_time)*100 e
         FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type AND
         DATE(start_time) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)
         AND DATE(UTC_TIMESTAMP() - INTERVAL 1 DAY)) week,

        (SELECT SUM(IF(err_count > :numerr, 1, 0))/COUNT(end_time)*100 e
         FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type AND
         DATE(start_time) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 62 DAY)
         AND DATE(UTC_TIMESTAMP() - INTERVAL 8 DAY)) week3;
        """)

        self.__examlist = self.sql("""SELECT
            exams.*, UTC_TIMESTAMP() > start_time + INTERVAL 3 HOUR,
            (CASE WHEN DATE(start_time) = DATE(UTC_TIMESTAMP())
            THEN 1 WHEN
                DATE(start_time) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)
                AND DATE(UTC_TIMESTAMP() - INTERVAL 1 DAY) THEN 2
            ELSE 3 END)
            FROM exams WHERE user_id=:user_id AND quiz_type=:quiz_type
            ORDER BY id DESC""")

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
        meta = exam_meta[quiz_type]
        numerr = meta['max_errors']
        try:
            row = self.__examstat.execute(user_id=user_id,
                                          quiz_type=quiz_type,
                                          numerr=numerr)
            row = row.fetchone()
        except Exception as e:
            print e
            row = (-1, -1, -1)
        return {
            'current': self._normErr(row[0]),
            'week': self._normErr(row[1]),
            'week3': self._normErr(row[2])
        }

    def getUserStat(self, quiz_type, user_id, lang):
        user = self._getStudentById(user_id)
        topics = self._getTopicsStat(quiz_type, user_id, lang)
        return {
            'student': user,
            'exams': self.__getExamStat(quiz_type, user_id),
            'topics': topics
        }

    def _createExamInfo(self, exam_db_row):
        quiz_type = exam_db_row[1]
        start = exam_db_row[3]
        end = exam_db_row[4]
        errors = exam_db_row[5]
        expired = exam_db_row[6]

        meta = exam_meta[quiz_type]
        numerr = meta['max_errors']

        if end:
            if errors > numerr:
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

    # TODO: not sure about performance
    def _getExamList(self, quiz_type, user_id, from_old_to_new):
        rows = self.__examlist.execute(user_id=user_id, quiz_type=quiz_type)
        current, week, week3 = [], [], []
        for row in rows:
            type = row[7]
            info = self._createExamInfo(row)
            if type == 1:
                current.append(info)
            elif type == 2:
                week.append(info)
            else:
                week3.append(info)
        if from_old_to_new:
            current = list(reversed(current))
            week = list(reversed(week))
            week3 = list(reversed(week3))
        return {'current': current, 'week': week, 'week3': week3}
        # rows = [self._createExamInfo(row) for row in rows]
        # return rows

    def getExamList(self, quiz_type, user_id, from_old_to_new=False):
        return {
            'student': self._getStudentById(user_id),
            'exams': self._getExamList(quiz_type, user_id, from_old_to_new)
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
