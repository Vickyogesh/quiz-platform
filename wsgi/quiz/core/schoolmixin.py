from sqlalchemy.exc import SQLAlchemyError, IntegrityError, StatementError
from .exceptions import QuizCoreError


class SchoolMixin(object):
    """This mixin provides school features. Used in QuizCore."""
    def __init__(self):
        self.__create = self.sql(self.users.insert().values(
                                 name=None, surname=None, login=None,
                                 passwd=None, school_id=0))

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
