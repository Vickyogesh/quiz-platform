from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError, StatementError
from .exceptions import QuizCoreError


class SchoolMixin(object):
    """This mixin provides school features. Used in QuizCore."""
    def __init__(self):
        self.__create = self.users.insert()
        self.__create = self.__create.values(name=None, surname=None,
                                             login=None, passwd=None,
                                             type='student', school_id=0)
        self.__create = self.__create.compile(self.engine)

    def _checkSchoolId(self, conn, school_id):
        t = self.users
        sel = t.select(and_(t.c.id == school_id, t.c.type == 'school'))
        res = conn.execute(sel).fetchone()
        if res is None:
            raise QuizCoreError('Unknown school.')

    def createStudent(self, name, surname, login, passwd, school):
        # Check if params are strings and they are not empty
        try:
            if len(name) == 0 or len(surname) == 0 or len(login) == 0\
               or len(passwd) == 0:
                raise QuizCoreError('Invalid parameters.')
        except TypeError:
            raise QuizCoreError('Invalid parameters.')

        try:
            with self.engine.begin() as conn:
                self._checkSchoolId(conn, school)
                res = conn.execute(self.__create, name=name, surname=surname,
                                   login=login, passwd=passwd, type='school',
                                   school_id=school)
                user_id = res.inserted_primary_key[0]
        except IntegrityError:
            raise QuizCoreError('Already exists.')
        except StatementError:
            raise QuizCoreError('Invalid parameters.')
        return {'id': user_id, 'name': name, 'surname': surname}
