from sqlalchemy import create_engine, MetaData, Table
from sqlalchemy import select, bindparam, text, and_
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
        verbose = cfg['verbose'].lower() == 'true'
        self.engine = create_engine(cfg['database'], echo=verbose)
        self.meta = MetaData()
        self.apps = Table('applications', self.meta, autoload=True,
                           autoload_with=self.engine)
        self.users = Table('users', self.meta, autoload=True,
                           autoload_with=self.engine)
        self.topics = Table('topics', self.meta, autoload=True,
                           autoload_with=self.engine)
        self.chapters = Table('chapters', self.meta, autoload=True,
                             autoload_with=self.engine)
        self.questions = Table('questions', self.meta, autoload=True,
                               autoload_with=self.engine)
        self.quiz_stat = Table('quiz_stat', self.meta, autoload=True,
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

        # See getQuiz() comments for more info.
        self._stmt_getquiz = text(
            """SELECT * FROM (SELECT * FROM questions WHERE id NOT IN (
            SELECT question_id FROM quiz_stat WHERE user_id=:user_id)
            AND topic_id=:topic_id LIMIT 100) t ORDER BY RAND() LIMIT 40;""")

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

    # Get 40 random questions from for the specified topic which are
    # not answered by the specified user.
    #
    # Query parts:
    # * how to get already answered quetions:
    #
    #       SELECT question_id FROM quiz_stat WHERE user_id=1;
    #
    # * how to filter out answered questions for the topic:
    #
    #       SELECT * FROM questions WHERE topic_id=1 AND
    #       id NOT IN (SELECT question_id FROM quiz_stat WHERE user_id=1);
    #
    # Result query:
    #
    #   SELECT * FROM (SELECT * FROM questions WHERE id NOT IN (
    #       SELECT question_id FROM quiz_stat WHERE user_id=1)
    #   AND topic_id=1 LIMIT 100) t ORDER BY RAND() LIMIT 40;
    #
    # NOTE: to increase ORDER BY RAND() we use very simple trick - just
    # limit subquery before ORDER with 100 rows which ORDER BY RAND()
    # must process fast enough. If this will be slow in the future then
    # rid it off and create somethin more tricky like:
    # http://explainextended.com/2009/03/01/selecting-random-rows
    # or
    # http://hudson.su/2010/09/16/mysql-optimizaciya-order-by-rand
    # http://jan.kneschke.de/projects/mysql/order-by-rand
    #
    # NOTE: another way to filter out answered questions (with JOIN):
    #
    #   SELECT * FROM questions q LEFT JOIN quiz_stat s
    #   ON q.id=s.question_id and s.user_id=1
    #   WHERE q.topic_id=1 and user_id is NULL;
    #
    def getQuiz(self, topic_id, user_id, lang):
        """ Return list of Quiz questions.

        Arguments:
        :param topic_id: Topic ID from which get questions for the Quiz.
        :param user_id: User ID for whom Quiz is generated.
        :param lang: Question language. Can be: (it, fr, de).

        Question is represented as a dictionary with the following items:
            id      - question ID in the DB
            text    - question text
            answer  - question answer (True/False)
            image   - image ID to illustrate the question (optional)
            image_bis - image type ID (optional)
        """
        res = self.conn.execute(self._stmt_getquiz,
                                topic_id=topic_id, user_id=user_id)
        if lang == 'de':
            txt_lang = self.questions.c.text_de
        elif lang == 'fr':
            txt_lang = self.questions.c.text_fr
        else:
            txt_lang = self.questions.c.text

        # TODO: maybe preallocate with quiz = [None] * 40?
        quiz = []
        for row in res:
            quiz.append({
                'id': int(row[self.questions.c.id]),
                'text': row[txt_lang],
                'answer': row[self.questions.c.answer],
                'image': row[self.questions.c.image],
                'image_bis': row[self.questions.c.image_part]
            })
        return quiz
