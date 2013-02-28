from sqlalchemy import create_engine, MetaData
from .usermixin import UserMixin
from .quizmixin import QuizMixin
from .exammixin import ExamMixin


# NOTE: to disable connection pool:
# from sqlalchemy.pool import NullPool
# self.engine = create_engine(cfg['database'], echo=verbose,
#                             poolclass=NullPool)

class QuizDb(UserMixin, QuizMixin, ExamMixin):
    """ High-level database operations. """

    def __init__(self, settings):
        self._setupDb(settings.dbinfo)
        UserMixin.__init__(self)
        QuizMixin.__init__(self)
        ExamMixin.__init__(self)

        # used in the _aux_question_delOptionalField()
        self.__optional_question_fields = ['image', 'image_bis']

    def __del__(self):
        print('close db connection')
        self.conn.close()

    # Setup db connection and tables
    def _setupDb(self, cfg):
        print('open connection')
        verbose = cfg['verbose'].lower() == 'true'
        self.engine = create_engine(cfg['database'], echo=verbose,)
        self.conn = self.engine.connect()

        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)

        self.apps = self.meta.tables['applications']
        self.users = self.meta.tables['users']
        self.chapters = self.meta.tables['chapters']
        self.topics = self.meta.tables['topics']
        self.questions = self.meta.tables['questions']
        self.quiz_stat = self.meta.tables['quiz_stat']

    # Remove None question fileds from the dict d.
    def _aux_question_delOptionalField(self, d):
        for x in self.__optional_question_fields:
            if d[x] is None:
                del d[x]
