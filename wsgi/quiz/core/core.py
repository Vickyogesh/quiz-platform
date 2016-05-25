from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.sql.expression import Insert
# from sqlalchemy import exc, event
# from sqlalchemy.pool import Pool

from .exceptions import QuizCoreError
from .usermixin import UserMixin
from .quizmixin import QuizMixin
from .exammixin import ExamMixin
from .reviewmixin import ErrorReviewMixin
from .guestmixin import GuestMixin
from .adminmixin import AdminMixin
from .schoolmixin import SchoolMixin


# http://stackoverflow.com/questions/15753102/python-sqlalchemy-how-do-i-ensure-connection-not-stale-using-new-event-system
# @event.listens_for(Pool, "checkout")
# def check_connection(dbapi_con, con_record, con_proxy):
#     """Listener for Pool checkout events that pings every
#     connection before using.

#     Implements pessimistic disconnect handling strategy. See also:
#     http://docs.sqlalchemy.org/en/rel_0_8/core/pooling.html#disconnect-handling-pessimistic
#     """

#     cursor = dbapi_con.cursor()
#     try:
#         cursor.execute("SELECT 1")  # could also be dbapi_con.ping(),
#                                     # not sure what is better
#     except exc.OperationalError, ex:
#         if ex.args[0] in (2006,   # MySQL server has gone away
#                           2013,   # Lost connection to MySQL server during query
#                           2055):  # Lost connection to MySQL server at '%s', system error: %d
#             # caught by pool, which will retry with a new connection
#             raise exc.DisconnectionError()
#         else:
#             raise


# http://stackoverflow.com/questions/6611563/sqlalchemy-on-duplicate-key-update
@compiles(Insert)
def append_string(insert, compiler, **kw):
    s = compiler.visit_insert(insert, **kw)
    if 'append_string' in insert.kwargs:
        return s + " " + insert.kwargs['append_string']
    return s


class QuizCore(UserMixin, QuizMixin, ErrorReviewMixin, ExamMixin, GuestMixin,
               AdminMixin, SchoolMixin):
    """This class provides core service logic.

    Logic is implemented by mixins:

    * :class:`.AdminMixin`
    * :class:`.ErrorReviewMixin`
    * :class:`.ExamMixin`
    * :class:`.GuestMixin`
    * :class:`.QuizMixin`
    * :class:`.SchoolMixin`
    * :class:`.UserMixin`

    It also provides access to the database. Structure of **Quiz Service** is
    creates by :file:`misc/dbinit.py` script. See also
    :file:`misc/dbtools/tables.py` and :file:`misc/dbtools/func.py`.

    .. attribute:: engine

        Core interface to the database.

    .. attribute:: meta

        Database metadata.

    Database tables:

    .. attribute:: apps

        ``applications`` table.

    .. attribute:: users

        ``users`` table.

    .. attribute:: chapters

        ``chapters`` table.

    .. attribute:: topics

        ``topics`` table.

    .. attribute:: questions

        ``questions`` table.

    .. attribute:: answers

        ``answers`` table.

    .. attribute:: quiz_answers

        ``quiz_answers`` table.

    .. attribute:: exam_answers

        ``exam_answers`` table.

    .. attribute:: exams

        ``exams`` table.

    .. attribute:: truck_last_sublicense

        ``truck_last_sublicense`` table (used by truck quiz).
    """
    def __init__(self, app):
        self._setupDb(app)
        UserMixin.__init__(self)
        QuizMixin.__init__(self)
        ErrorReviewMixin.__init__(self)
        ExamMixin.__init__(self)
        GuestMixin.__init__(self)
        AdminMixin.__init__(self)
        SchoolMixin.__init__(self)

        # used in the _aux_question_delOptionalField()
        self.__optional_question_fields = ['image', 'image_bis']
        self.guest_allowed_requests = app.config['GUEST_ALLOWED_REQUESTS']

    # Setup db connection and tables
    # NOTE: MySQL features an automatic connection close behavior,
    # for connections that have been idle for eight hours or more.
    # See:
    # http://docs.sqlalchemy.org/en/rel_0_8/dialects/mysql.html#connection-timeouts
    # http://www.sqlalchemy.org/trac/wiki/FAQ#MySQLserverhasgoneaway
    def _setupDb(self, app):
        verbose = app.config.get('SQLALCHEMY_ECHO', False)
        uri = app.config['SQLALCHEMY_DATABASE_URI']
        self.engine = create_engine(uri, echo=verbose, pool_recycle=3600)

        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)

        self.apps = self.meta.tables['applications']
        self.users = self.meta.tables['users']
        self.chapters = self.meta.tables['chapters']
        self.topics = self.meta.tables['topics']
        self.questions = self.meta.tables['questions']
        self.blacklist = self.meta.tables['blacklist']
        self.answers = self.meta.tables['answers']
        self.quiz_answers = self.meta.tables['quiz_answers']
        self.exam_answers = self.meta.tables['exam_answers']
        self.exams = self.meta.tables['exams']
        self.truck_last_sublicense = self.meta.tables['truck_last_sublicense']
        self.stat_json = self.meta.tables['stat_json']

    def sql(self, stmt):
        """Compile SQL expression."""
        if isinstance(stmt, str) or isinstance(stmt, unicode):
            stmt = text(' '.join(stmt.split()))
        return stmt.compile(self.engine)

    # Remove None question fileds from the dict d.
    def _aux_question_delOptionalField(self, d):
        for x in self.__optional_question_fields:
            if d[x] is None:
                del d[x]

    def _aux_prepareLists(self, questions, answers):
        try:
            if len(questions) != len(answers):
                raise QuizCoreError('Parameters length mismatch.')
            elif not answers:
                raise QuizCoreError('Empty list.')
        except QuizCoreError:
            raise
        except Exception:
            raise QuizCoreError('Invalid value.')

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
