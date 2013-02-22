from sqlalchemy import select, bindparam, and_


class UserMixin(object):
    """ Mixin for working with user information. Used in QuizDb. """
    def __init__(self):
        users = self.users
        apps = self.apps

        query = select(
            [users.c.id, users.c.passwd, users.c.type, apps.c.id],
            and_(users.c.login == bindparam('login'),
                 apps.c.appkey == bindparam('appkey')),
            use_labels=True
        )
        self.__stmt = query.compile(self.engine)

    def getInfo(self, login, appkey):
        """ Return user and application info.

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
        res = self.conn.execute(self.__stmt, login=login, appkey=appkey)
        row = res.fetchone()

        if row:
            return {
                'user_id': row[self.users.c.id],
                'passwd': row[self.users.c.passwd],
                'type': row[self.users.c.type],
                'app_id': row[self.apps.c.id]
            }
