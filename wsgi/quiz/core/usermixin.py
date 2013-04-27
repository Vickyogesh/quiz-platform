from sqlalchemy import select, text, bindparam, and_
from sqlalchemy.exc import SQLAlchemyError
from .exceptions import QuizCoreError


class UserMixin(object):
    """Mixin for working with user information. Used in QuizCore."""
    def __init__(self):
        apps = self.apps
        users = self.users

        self.__appid = self.sql("""SELECT id FROM applications
                                WHERE appkey=:appkey""")

        self.__school = self.sql("SELECT * FROM schools WHERE login=:login")

        self.__user_by_login = self.sql("SELECT * FROM users WHERE login=:login")

        self.__user_by_id = self.sql("SELECT * FROM users WHERE id=:id")

        self.__stmt = self.sql(select(
            [users.c.id, users.c.name, users.c.surname,
             users.c.passwd, users.c.type, apps.c.id],
            and_(users.c.login == bindparam('login'),
                 apps.c.appkey == bindparam('appkey')),
            use_labels=True))

        self.__getname = self.sql(select(
            [users.c.name, users.c.surname, users.c.type],
            users.c.id == bindparam('id')))

        self.__topicstat = self.sql("""SELECT
            t.id, t.text, t.text_fr, t.text_de,
            IFNULL((SELECT err_count/count*100 FROM topic_err_current WHERE
                user_id=:user_id AND topic_id=t.id), -1) current,
            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND topic_id = t.id AND
               now_date BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 7 DAY
               AND DATE(UTC_TIMESTAMP()) - INTERVAL 1 DAY
               GROUP BY topic_id), -1) week,
            IFNULL((SELECT avg(err_percent) FROM topic_err_snapshot WHERE
               user_id=:user_id AND topic_id = t.id AND
               now_date BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 29 DAY
               AND DATE(UTC_TIMESTAMP()) - INTERVAL 8 DAY
               GROUP BY topic_id), -1) week3
            from topics t""")

        # NOTE: we skip 'in-progress' exams.
        self.__examstat = self.sql("""SELECT
            (SELECT SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100 e
             FROM exams WHERE user_id=:user_id) current,
            (SELECT SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100 e
             FROM exams WHERE user_id=:user_id AND
             start_time BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 7 DAY
             AND DATE(UTC_TIMESTAMP()) - INTERVAL 1 DAY) week,
            (SELECT SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100 e
             FROM exams WHERE user_id=:user_id AND
             start_time BETWEEN DATE(UTC_TIMESTAMP()) - interval 29 day
             AND DATE(UTC_TIMESTAMP()) - INTERVAL 8 DAY) week3;
            """)

        self.__examlist = self.sql("""SELECT
            exams.*, UTC_TIMESTAMP() > start_time + INTERVAL 3 HOUR
            FROM exams WHERE user_id=:user_id;""")

        self.__topicerr = self.sql("""SELECT
            * FROM (SELECT * FROM questions WHERE topic_id=:topic_id
            AND id IN (SELECT question_id FROM answers WHERE
            user_id=:user_id AND is_correct=0)) t;""")

        self.__lastvisit = self.sql("""UPDATE
            users SET last_visit=UTC_TIMESTAMP() WHERE id=:user_id""")

    def updateUserLastVisit(self, user_id):
        self.engine.execute(self.__lastvisit, user_id=user_id)

    def getAppId(self, appkey):
        try:
            row = self.__appid.execute(appkey=appkey).fetchone()
        except SQLAlchemyError:
            row = None
        if row is None:
            raise QuizCoreError('Unknown application ID.')
        return row[0]

    def _getSchoolByLogin(self, login, with_passwd=False):
        try:
            row = self.__school.execute(login=login).fetchone()
        except SQLAlchemyError:
            row = None
        if row is None:
            raise QuizCoreError('Unknown school.')
        d = {'id': row[0], 'name': row[1], 'login': row[2], 'type': 'school'}
        if with_passwd:
            d['passwd'] = row[3]
        return d

    def __studentFromRow(self, row, with_passwd):
        d = {'id': row[0], 'name': row[1], 'surname': row[2],
             'login': row[3], 'type': row[5], 'school_id': row[6]}
        if with_passwd:
            d['passwd'] = row[4]
        return d

    def _getStudentById(self, user_id, with_passwd=False):
        try:
            row = self.__user_by_id.execute(id=user_id).fetchone()
        except SQLAlchemyError:
            row = None
        if row is None:
            raise QuizCoreError('Unknown student.')
        return self.__studentFromRow(row, with_passwd)

    def _getStudentByLogin(self, login, with_passwd=False):
        try:
            row = self.__user_by_login.execute(login=login).fetchone()
        except SQLAlchemyError:
            row = None
        if row is None:
            raise QuizCoreError('Unknown student.')
        return self.__studentFromRow(row, with_passwd)

    def getUserInfo(self, login, with_passwd=False):
        if login == 'admin':
            d = {
                'id': 0,
                'name': 'admin',
                'login': 'admin',
                'type': 'admin',
            }
            if with_passwd:
                d['passwd'] = self.admin_passwd
            return d

        info = None
        try:
            info = self._getStudentByLogin(login, with_passwd)
        except QuizCoreError:
            try:
                info = self._getSchoolByLogin(login, with_passwd)
            except QuizCoreError:
                pass
        if info is None:
            raise QuizCoreError('Unknown user.')
        return info

    def _normErr(self, err):
        if err is None:
            return -1
        elif 0 < err < 1:
            return 1
        elif 99 < err < 100:
            return 99
        return round(err)

    def _getTopicsStat(self, user, lang):
        if lang == 'de':
            lang = 3
        elif lang == 'fr':
            lang = 2
        else:
            lang = 1

        # TODO: maybe preallocate with stat = [None] * x?
        stat = []
        rows = self.__topicstat.execute(user_id=user)
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

    def __getExamStat(self, user_id):
        try:
            row = self.__examstat.execute(user_id=user_id).fetchone()
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

    def getUserStat(self, user_id, lang):
        user = self._getStudentById(user_id)
        topics = self._getTopicsStat(user_id, lang)
        return {
            'student': user,
            'exams': self.__getExamStat(user_id),
            'topics': topics
        }

    def _createExamInfo(self, exam_db_row):
        start = exam_db_row[2]
        end = exam_db_row[3]
        errors = exam_db_row[4]
        expired = exam_db_row[5]

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

    def _getExamList(self, user_id):
        rows = self.__examlist.execute(user_id=user_id)
        return [self._createExamInfo(row) for row in rows]

    def getExamList(self, user_id):
        return {
            'student': self._getStudentById(user_id),
            'exams': self._getExamList(user_id)
        }

    def getTopicErrors(self, user_id, topic_id, lang):
        student = self._getStudentById(user_id)

        rows = self.__topicerr.execute(user_id=user_id, topic_id=topic_id)

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
