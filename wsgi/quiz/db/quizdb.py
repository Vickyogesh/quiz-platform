from sqlalchemy import create_engine, MetaData
from .usermixin import UserMixin
from .quizmixin import QuizMixin


class QuizDb(UserMixin, QuizMixin):
    """ High-level database operations. """

    def __init__(self, settings):
        self._setupDb(settings.dbinfo)
        UserMixin.__init__(self)
        QuizMixin.__init__(self)

    def __del__(self):
        self.conn.close()

    # Setup db connection and tables
    def _setupDb(self, cfg):
        verbose = cfg['verbose'].lower() == 'true'
        self.engine = create_engine(cfg['database'], echo=verbose)
        self.conn = self.engine.connect()

        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)

        self.apps = self.meta.tables['applications']
        self.users = self.meta.tables['users']
        self.chapters = self.meta.tables['chapters']
        self.topics = self.meta.tables['topics']
        self.questions = self.meta.tables['questions']
        self.quiz_stat = self.meta.tables['quiz_stat']
