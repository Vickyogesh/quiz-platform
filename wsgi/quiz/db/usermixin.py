from sqlalchemy import select, text, bindparam, and_
from quiz.exceptions import QuizCoreError


class UserMixin(object):
    """ Mixin for working with user information. Used in QuizDb. """
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
            SELECT t.id, t.text, t.text_fr, t.text_de, IFNULL(s.err_count,-1)
            FROM topics t LEFT JOIN
            (SELECT * FROM topics_stat WHERE user_id=:user_id) s
            ON t.id=s.topic_id;""")
        self.__topicstat = self.__topicstat.compile(self.engine)

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
                'name': row[self.users.c.name],
                'surname': row[self.users.c.surname],
                'passwd': row[self.users.c.passwd],
                'type': row[self.users.c.type],
                'app_id': row[self.apps.c.id]
            }

    def _getName(self, user):
        row = self.conn.execute(self.__getname, id=user)
        row = row.fetchone()
        if not row:
            raise QuizCoreError('Unknown student.')
        elif row[2] != 'student':
            raise QuizCoreError('Not a student.')
        return row[0], row[1]

    def _getTopicsStat(self, user, lang):
        if lang == 'de':
            lang = 3
        elif lang == 'fr':
            lang = 2
        else:
            lang = 1

        # TODO: maybe preallocate with stat = [None] * x?
        stat = []
        rows = self.conn.execute(self.__topicstat, user_id=user)
        for row in rows:
            stat.append({
                'id': row[0],
                'text': row[lang],
                'errors': int(row[4])
            })
        return stat

    def getUserStat(self, user, lang):
        name, surname = self._getName(user)
        if name is None:
            return {}

        return {
            'id': user,
            'name': name,
            'surname': surname,
            'topics': self._getTopicsStat(user, lang)
        }
