try:
    import simplejson as json
except ImportError:
    import json

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, StatementError
from .exceptions import QuizCoreError


class SchoolMixin(object):
    """This mixin provides school features. Used in QuizCore."""
    def __init__(self):
        self.__create = self.sql(self.users.insert().values(
                                 name=None, surname=None, login=None,
                                 passwd=None, school_id=0))

        self.__topics = self.sql("""SELECT t.id, t.text, t.text_fr, t.text_de,
        IFNULL((SELECT err_count/count*100 FROM school_topic_err WHERE
               school_id=:school_id AND topic_id=t.id), -1) current,
        IFNULL((SELECT avg(err_percent) FROM school_topic_err_snapshot WHERE
               school_id=:school_id AND topic_id = t.id AND
               now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 7 day
               AND DATE(UTC_TIMESTAMP())
               GROUP BY topic_id), -1) week,
        IFNULL((SELECT avg(err_percent) FROM school_topic_err_snapshot WHERE
               school_id=:school_id AND topic_id = t.id AND
               now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 29 day
               AND DATE(UTC_TIMESTAMP()) - interval 8 day
               GROUP BY topic_id), -1) week3
        from topics t;""")

        # self.__topics = self.sql("""SELECT t.id, t.text, t.text_fr, t.text_de,
        #     IFNULL(s.err_count/s.count*100, -1),
        #     IFNULL(s.err_week, -1),
        #     IFNULL(s.err_week3, -1)
        #     FROM topics t LEFT JOIN school_topic_err s
        #     ON t.id=s.topic_id AND school_id=:school_id""")

        self.__cache = self.sql("""SELECT
            stat_cache FROM school_stat_cache WHERE school_id=:school_id""")

    def _checkSchoolId(self, school_id):
        try:
            t = self.schools
            sel = t.select(t.c.id == school_id)
            res = self.engine.execute(sel).fetchone()
        except SQLAlchemyError:
            res = None

        if res is None:
            raise QuizCoreError('Invalid school ID.')

    def createStudent(self, name, surname, login, passwd, school):
        # Check if params are strings and they are not empty
        try:
            if len(name) == 0 or len(surname) == 0 or len(login) == 0\
               or len(passwd) == 0:
                raise QuizCoreError('Invalid parameters.')
        except TypeError:
            raise QuizCoreError('Invalid parameters.')

        try:
            self._checkSchoolId(school)
            with self.engine.begin() as conn:
                res = conn.execute(self.__create, name=name, surname=surname,
                                   login=login, passwd=passwd,
                                   school_id=school)
                user_id = res.inserted_primary_key[0]
        except IntegrityError:
            raise QuizCoreError('Already exists.')
        except StatementError:
            raise QuizCoreError('Invalid parameters.')
        return {'id': user_id, 'name': name, 'surname': surname}

    def getStudentList(self, school_id):
        self._checkSchoolId(school_id)

        t = self.users
        sel = t.select(t.c.school_id == school_id)
        res = self.engine.execute(sel)
        lst = [{'id': r[0], 'name': r[1], 'surname': r[2], 'login': r[3],
                'type': r[5]} for r in res]
        return {'students': lst}

    def deleteStudent(self, school_id, student_id):
        self._checkSchoolId(school_id)

        user = self._getStudentById(student_id)
        if user['school_id'] != school_id:
            raise QuizCoreError('Unknown student.')

        dl = self.users.delete().where(self.users.c.id == student_id)
        self.engine.execute(dl)
        return {}

    def __getSchoolTopics(self, school_id, lang):
        if lang == 'de':
            lang = 3
        elif lang == 'fr':
            lang = 2
        else:
            lang = 1

        topics = []
        rows = self.__topics.execute(school_id=school_id)
        for row in rows:
            topics.append({
                'id': row[0],
                'text': row[lang],
                'errors': {
                    'current': self._normErr(row[4]),
                    'week': self._normErr(row[5]),
                    'week3': self._normErr(row[6])
                }
            })
        return topics

    def getSchoolStat(self, school_id, lang):
        topics = self.__getSchoolTopics(school_id, lang)
        stat = self.__cache.execute(school_id=school_id).fetchone()

        try:
            stat = json.loads(stat[0])
            data = {
                'topics': topics,
                'students': {
                    'current': stat['current'],
                    'week': stat['week'],
                    'week3': stat['week3']
                },
                'guest_visits': stat['guest_visits'],
                'exams': stat['exams']
            }
        except Exception:
            data = {
                'topics': topics,
                'students': {
                    'current': [],
                    'week': [],
                    'week3': []
                },
                'guest_visits': [],
                'exams': []
            }
        return data
