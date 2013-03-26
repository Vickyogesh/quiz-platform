from sqlalchemy import select, text, bindparam, and_
from .exceptions import QuizCoreError


class UserMixin(object):
    """Mixin for working with user information. Used in QuizCore."""
    def __init__(self):
        users = self.users
        apps = self.apps

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

    def getUserAndAppInfo(self, login, appkey):
        """Return user and application info.

        Args:
            login:  User's login
            appkey: Application key

        Returns:
            Dict with the following keys:
                user_id: ID in the database.
                passwd:  Password (md5 hash).
                type:    Account type.
                app_pd:  Application ID.
        """
        if login == 'admin':
            res = self.engine.execute(text("SELECT id FROM applications WHERE appkey=:k"),
                                      k=appkey).fetchone()
            return {
                'user_id': 0,
                'name': 'admin',
                'surname': None,
                'passwd': self.admin_passwd,
                'type': 'admin',
                'app_id': res[0]
            }

        res = self.__stmt.execute(login=login, appkey=appkey)
        row = res.fetchone()

        if row:
            return {
                'user_id': row[self.users.c.id],
                'name': row[self.users.c.name],
                'surname': row[self.users.c.surname],
                'passwd': row[self.users.c.passwd],
                'type': row[self.users.c.type],
                'app_id': row[self.apps.c.id]
            }

    def _getStudentInfo(self, user_id):
        row = self.__getname.execute(id=user_id)
        row = row.fetchone()

        if row is None:
            raise QuizCoreError('Unknown student.')
        elif row[2] != 'student' and row[2] != 'guest':
            raise QuizCoreError('Not a student.')
        return {'id': user_id, 'name': row[0], 'surname': row[1]}

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
        user = self._getStudentInfo(user_id)
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
            'student': self._getStudentInfo(user_id),
            'exams': self._getExamList(user_id)
        }

    def getTopicErrors(self, user_id, topic_id, lang):
        student = self._getStudentInfo(user_id)

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
