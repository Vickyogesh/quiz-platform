from sqlalchemy import *
from sqlalchemy.sql import func


class QuizDb(object):
    """ High-level database operations. """

    def __init__(self, settings):
        self._setupDb(settings.dbinfo)

    def __del__(self):
        #print('close')
        self.conn.close()

    # Setup db connection, tables and query statements
    def _setupDb(self, cfg):
        self.engine = create_engine(cfg['database'], echo=cfg['verbose'] == 'True')
        self.meta = MetaData()
        self.apps = Table('applications', self.meta, autoload=True,
                           autoload_with=self.engine)
        self.users = Table('users', self.meta, autoload=True,
                           autoload_with=self.engine)
        self.topic = Table('topic', self.meta, autoload=True,
                           autoload_with=self.engine)
        self.chapter = Table('chapter', self.meta, autoload=True,
                             autoload_with=self.engine)
        self.questions = Table('questions', self.meta, autoload=True,
                               autoload_with=self.engine)
        self.conn = self.engine.connect()
        self._prepare_stmt()

    def _prepare_stmt(self):
        users = self.users
        apps = self.apps
        questions = self.questions

        query = select(
            [users.c.id, users.c.passwd, users.c.type, apps.c.id],
            and_(users.c.login == bindparam('login'),
                 apps.c.appkey == bindparam('appkey')),
            use_labels=True
        )
        self._stmt_user = query.compile(self.engine)

        query = select([questions], questions.c.topic_id == bindparam('topic'))
        query = query.order_by(func.random()).limit(40)
        self._stmt_quiz = query.compile(self.engine)

    def getInfo(self, login, appkey):
        """ Return user and application info. """
        res = self.conn.execute(self._stmt_user, login=login, appkey=appkey)
        row = res.fetchone()

        if row:
            return {
                'user_id': row[self.users.c.id],
                'passwd': row[self.users.c.passwd],
                'type': row[self.users.c.type],
                'app_id': row[self.apps.c.id]
            }

    def getQuiz(self, topic_id, lang, num):
        """
        Return list of :num questions.
        Question is represented as a dictionary with the following items:
            id      - question ID in the DB
            text    - question text
            answer  - question answer (True/False)
            image   - image ID to illustrate the question (optional)
            image_bis - image type ID (optional)
        """
        res = self.conn.execute(self._stmt_quiz, topic=topic_id, param_1=num)
        if lang == 'de':
            c = self.questions.c.text_de
        elif lang == 'fr':
            c = self.questions.c.text_fr
        else:
            c = self.questions.c.text

        quiz = []
        for row in res:
            quiz.append({
                'id': row[self.questions.c.id],
                'text': row[c],
                'answer': row[self.questions.c.answer],
                'image': row[self.questions.c.image],
                'image_bis': row[self.questions.c.image_part]
            })
        return quiz
