from sqlalchemy import select, text, bindparam, and_
from .exceptions import QuizCoreError


class UserMixin(object):
    """Mixin for working with user information. Used in QuizCore."""
    def __init__(self):
        apps = self.apps
        users = self.users

        self.__appid = text("SELECT id FROM applications WHERE appkey=:appkey")
        self.__appid = self.__appid.compile(self.engine)

        self.__school = text("SELECT * FROM schools WHERE login=:login")
        self.__school = self.__school.compile(self.engine)

        self.__user_by_login = text("SELECT * FROM users WHERE login=:login")
        self.__user_by_login = self.__user_by_login.compile(self.engine)

        self.__user_by_id = text("SELECT * FROM users WHERE id=:id")
        self.__user_by_id = self.__user_by_id.compile(self.engine)

        query = select(
            [users.c.id, users.c.name, users.c.surname, users.c.passwd, users.c.type, apps.c.id],
            and_(users.c.login == bindparam('login'),
                 apps.c.appkey == bindparam('appkey')),
            use_labels=True
        )
        self.__stmt = query.compile(self.engine)

        self.__getname = select([users.c.name, users.c.surname, users.c.type], users.c.id == bindparam('id'))
        self.__getname = self.__getname.compile(self.engine)

        self.__topicstat = text("""
            SELECT t.id, t.max_id - t.min_id + 1, t.text, t.text_fr, t.text_de,
            IFNULL(s.err_count,-1) FROM topics t LEFT JOIN
            (SELECT * FROM topics_stat WHERE user_id=:user_id) s
            ON t.id=s.topic_id;""")
        self.__topicstat = self.__topicstat.compile(self.engine)

        self.__examstat = text("""SELECT id, err_count, end_time,
            UTC_TIMESTAMP() > start_time + interval 3 hour
            FROM exams WHERE user_id=:user_id;""")
        self.__examstat = self.__examstat.compile(self.engine)

        self.__examlist = text("""SELECT exams.*,
            UTC_TIMESTAMP() > start_time + interval 3 hour
            FROM exams WHERE user_id=:user_id;""")
        self.__examlist = self.__examlist.compile(self.engine)

        self.__topicerr = text(
            """SELECT * FROM (SELECT * FROM questions WHERE topic_id=:topic_id
            AND id IN (SELECT question_id FROM errors WHERE
            user_id=:user_id)) t;""")
        self.__topicerr = self.__topicerr.compile(self.engine)

        self.__lastvisit = text("""UPDATE users SET last_visit=UTC_TIMESTAMP()
                                WHERE id=:user_id""")
        self.__lastvisit = self.__lastvisit.compile(self.engine)

    def updateUserLastVisit(self, user_id):
        self.engine.execute(self.__lastvisit, user_id=user_id)

    def getAppId(self, appkey):
        res = self.__appid.execute(appkey=appkey).fetchone()
        if res is None:
            raise QuizCoreError('Unknown application ID.')
        return res[0]

    def _getSchoolByLogin(self, login, with_passwd=False):
        row = self.__school.execute(login=login).fetchone()
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
        row = self.__user_by_id.execute(id=user_id).fetchone()
        if row is None:
            raise QuizCoreError('Unknown student.')
        return self.__studentFromRow(row, with_passwd)

    def _getStudentByLogin(self, login, with_passwd=False):
        row = self.__user_by_login.execute(login=login).fetchone()
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

    def _getTopicsStat(self, user, lang):
        if lang == 'de':
            lang = 4
        elif lang == 'fr':
            lang = 3
        else:
            lang = 2

        # TODO: maybe preallocate with stat = [None] * x?
        stat = []
        rows = self.__topicstat.execute(user_id=user)
        for row in rows:
            err = float(row[5]) / row[1] * 100

            if err < 0:
                err = -1
            elif 0 < err < 1:
                err = 1
            elif 99 < err < 100:
                err = 99

            stat.append({
                'id': row[0],
                'text': row[lang],
                'errors': int(err)
            })
        return stat

    def __getExamStat(self, user_id):
        rows = self.__examstat.execute(user_id=user_id)
        stat = []
        for row in rows:
            end = row[2]
            expired = row[3]
            if end:
                stat.append({'id': row[0], 'status': row[1]})
            elif expired:
                stat.append({'id': row[0], 'status': 'expired'})
            else:
                stat.append({'id': row[0], 'status': 'in-progress'})
        return stat

    def getUserStat(self, user_id, lang):
        user = self._getStudentById(user_id)
        return {
            'student': user,
            'exams': self.__getExamStat(user_id),
            'topics': self._getTopicsStat(user_id, lang)
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
