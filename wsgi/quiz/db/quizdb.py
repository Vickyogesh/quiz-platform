from quiz.exceptions import QuizCoreError
from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
from .usermixin import UserMixin
from .quizmixin import QuizMixin
from .exammixin import ExamMixin
from .reviewmixin import ErrorReviewMixin


# http://stackoverflow.com/questions/6611563/sqlalchemy-on-duplicate-key-update
@compiles(Insert)
def append_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    if 'append_string' in insert.kwargs:
        return s + " " + insert.kwargs['append_string']
    return s


# NOTE: to disable connection pool:
# from sqlalchemy.pool import NullPool
# self.engine = create_engine(cfg['database'], echo=verbose,
#                             poolclass=NullPool)

class QuizDb(UserMixin, QuizMixin, ErrorReviewMixin, ExamMixin):
    """ High-level database operations. """

    def __init__(self, settings):
        self._setupDb(settings.dbinfo)
        UserMixin.__init__(self)
        QuizMixin.__init__(self)
        ErrorReviewMixin.__init__(self)
        ExamMixin.__init__(self)

        # used in the _aux_question_delOptionalField()
        self.__optional_question_fields = ['image', 'image_bis']

    # def __del__(self):
    #     self.conn.close()

    # Setup db connection and tables
    def _setupDb(self, cfg):
        verbose = cfg['verbose'].lower() == 'true'
        self.engine = create_engine(cfg['database'], echo=verbose,)

        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)

        self.apps = self.meta.tables['applications']
        self.users = self.meta.tables['users']
        self.chapters = self.meta.tables['chapters']
        self.topics = self.meta.tables['topics']
        self.questions = self.meta.tables['questions']
        self.answers = self.meta.tables['answers']
        self.exams = self.meta.tables['exams']
        self.exams_stat = self.meta.tables['exams_stat']

    # Remove None question fileds from the dict d.
    def _aux_question_delOptionalField(self, d):
        for x in self.__optional_question_fields:
            if d[x] is None:
                del d[x]

    def _aux_prepareLists(self, questions, answers):
        if len(questions) != len(answers):
            raise QuizCoreError('Parameters length mismatch.')

        # questions must contain integer values since it represents
        # list of IDs. It's important to have valid list
        # because select will skip bad values and answers
        # will not correspond to rows.
        #
        # Since sqlalchemy in_() accept iterable object
        # we may use generator here.
        questions = (int(x) for x in questions)
        answers = (int(x) for x in answers)

        # TODO: seems not very optimal way since it creates many list objects.
        #
        # We need sorted list of answers to correctly compare in the
        # 'for row, answer in zip(res, answers)' later, since db server
        # will return sorted list of questions' IDs.
        # See also test_saveUnordered() test in the tests/test_db_quiz.py
        try:
            lst = list(sorted(zip(questions, answers), key=lambda pair: pair[0]))
            questions, answers = zip(*lst)
        except ValueError:
            raise QuizCoreError('Invalid value.')
        return questions, answers
