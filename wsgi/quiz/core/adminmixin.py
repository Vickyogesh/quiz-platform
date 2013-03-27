import hashlib
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, StatementError
from .exceptions import QuizCoreError


class AdminMixin(object):
    """This mixin provides administration features. Used in QuizCore."""
    def __init__(self):
        self.__create = self.users.insert()
        self.__create = self.__create.values(name=None, surname=None, login=None,
                                             passwd=None, type='school',
                                             school_id=0)
        self.__create = self.__create.compile(self.engine)

        t = self.users
        self.__list = t.select(t.c.type == 'school')
        self.__list = self.__list.compile(self.engine)

    def __create_guest_passwd(self, login):
        m = hashlib.md5()
        m.update('%s:guest' % login)
        return m.hexdigest()

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

                # We aslo add guest user for this
                guest_login = login + '-guest'
                conn.execute(self.__create, name=name, surname='',
                             login=guest_login,
                             passwd=self.__create_guest_passwd(guest_login),
                             type='guest', school_id=school_id)
        except IntegrityError:
            raise QuizCoreError('Already exists.')
        except StatementError:
            raise QuizCoreError('Invalid parameters.')
        return {'id': school_id}

    def getSchoolList(self):
        res = self.__list.execute()
        lst = [{'id': row[0], 'name': row[1], 'login': row[3]} for row in res]
        return {'schools': lst}

    # TODO: test me
    def deleteSchool(self, id):
        # Check if this is school id.
        # See SchoolMixin._checkSchoolId().
        self._checkSchoolId(id)

        # We have to remove all related data like students and their data.
        t = self.users
        dl = t.delete().where(or_(t.c.id == id, t.c.school_id == id))
        self.engine.execute(dl)
