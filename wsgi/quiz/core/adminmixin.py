from sqlalchemy.exc import IntegrityError, StatementError
from .exceptions import QuizCoreError


class AdminMixin(object):
    """This mixin provides administration features. Used in QuizCore."""
    def __init__(self):
        self.__create = self.sql(self.schools.insert().values(
                                 name=None, login=None, passwd=None))
        self.__list = self.sql(self.schools.select())

    def createSchool(self, name, login, passwd):
        # Check if params are strings and they are not empty
        try:
            if len(name) == 0 or len(login) == 0 or len(passwd) == 0:
                raise QuizCoreError('Invalid parameters.')
        except TypeError:
            raise QuizCoreError('Invalid parameters.')

        try:
            with self.engine.begin() as conn:
                # NOTE: guest will be created by the trigger.
                # See _createFuncs() in the misc/dbtools.py
                res = conn.execute(self.__create, name=name, login=login,
                                   passwd=passwd)
                school_id = res.inserted_primary_key[0]
        except IntegrityError:
            raise QuizCoreError('Already exists.')
        except StatementError:
            raise QuizCoreError('Invalid parameters.')
        return {'id': school_id}

    def getSchoolList(self):
        res = self.__list.execute()
        lst = [{'id': row[0], 'name': row[1], 'login': row[2]} for row in res]
        return {'schools': lst}

    # NOTE: triggers will delete school's users and
    # their data on school delete.
    # See _createFuncs() in the misc/dbtools.py
    def deleteSchool(self, id):
        # Check if this is school id.
        # See SchoolMixin._checkSchoolId().
        self._checkSchoolId(id)

        # We have to remove all related data like students and their data.
        t = self.schools
        dl = t.delete().where(t.c.id == id)
        self.engine.execute(dl)
        return {}