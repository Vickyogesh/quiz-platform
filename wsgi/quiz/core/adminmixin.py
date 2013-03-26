from sqlalchemy import text
from sqlalchemy.exc import IntegrityError, StatementError
from .exceptions import QuizCoreError


class AdminMixin(object):
    """This mixin provides administration features. Used in QuizCore."""
    def __init__(self):
        self.__create = self.users.insert()
        self.__create = self.__create.values(name=None, surname=None, login=None,
                                             passwd=None, type='school')
        self.__create = self.__create.compile(self.engine)

    def createSchool(self, name, login, passwd):
        # Check if params are strings and they are not empty
        try:
            if len(name) == 0 or len(login) == 0 or len(passwd) == 0:
                raise QuizCoreError('Invalid parameters.')
        except TypeError:
            raise QuizCoreError('Invalid parameters.')

        try:
            with self.engine.begin() as conn:
                res = conn.execute(self.__create, name=name, surname='',
                                   login=login, passwd=passwd, type='school')
                school_id = res.inserted_primary_key[0]
        except IntegrityError:
            raise QuizCoreError('Already exists.')
        except StatementError:
            raise QuizCoreError('Invalid parameters.')
        return {'id': school_id}
