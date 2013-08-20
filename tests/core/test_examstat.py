# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
from datetime import datetime, timedelta
from tests_common import db_uri, cleanupdb_onSetup, cleanupdb_onTearDown
from sqlalchemy import select
from quiz.core.core import QuizCore
from quiz.core.exceptions import QuizCoreError
from test_exam import pass_exam


def print_exams(tst):
    res = tst.sql('select * from exams')
    for row in res:
        id = row[0]
        s = row[3].strftime("%d.%m.%Y %H:%M:%S")
        e = row[4].strftime("%d.%m.%Y %H:%M:%S") if row[4] else '--'
        err = row[5]
        print id, s, e, err


# Create exams for the month (29 days) + 4 days,
# each day will contain 3 exams.
# Return list of generated dates for each period (current, week, week3)
def create_exams(tst):
    start = datetime.utcnow()
    lst = []
    current, week, week3 = [], [], []

    # recent (2 last days): 4 passed, 2 in progress, 2 failed (total 8).
    for i in xrange(2):
        exam_time = start
        for j in xrange(4):
            exam_time += timedelta(hours=1)
            lst.append({'quiz_type': 1, 'user_id': 1,
                       'start_time': exam_time,
                       'end_time': None if j == 1 else exam_time,
                       'err_count': 0 if j == 1 else 2 + j})
            current.append(start.date().strftime('%Y-%m-%d'))
        start -= timedelta(days=1)

    # last week data (including recent days):
    # 7 in progress, 12 failed (total exams 28).
    for i in xrange(5):  # 7days - 2 recent days
        exam_time = start
        for j in xrange(4):
            exam_time += timedelta(hours=1)
            lst.append({'quiz_type': 1, 'user_id': 1,
                       'start_time': exam_time,
                       'end_time': None if j == 1 else exam_time,
                       'err_count': 0 if j == 1 else 4 + j})
            week.append(start.date().strftime('%Y-%m-%d'))
        start -= timedelta(days=1)


    # 3 weeks (before last week) 3 * 7 = 21 days + 3 extra day:
    # 5 errors, 1 in progress, the rest are passed (total 21).
    # one exam per day.
    for i in xrange(24):
        exam_time = start + timedelta(hours=1)
        lst.append({'quiz_type': 1, 'user_id': 1,
                   'start_time': exam_time,
                   'end_time': None if i == 6 else exam_time,
                   'err_count': 12 if i < 5 else 0})
        week3.append(start.date().strftime('%Y-%m-%d'))
        start -= timedelta(days=1)
    tst.sql(tst.core.exams.insert(), lst)
    return current, week, week3

# Test: generate exam, save exam, exam's errors counting.
class ExamStatTest(unittest.TestCase):
    def setUp(self):
        self.dbinfo = {'database': db_uri, 'verbose': 'false'}
        self.main = {'guest_allowed_requests': 10}
        self.core = QuizCore(self)
        self.questions = self.core.questions
        self.engine = self.core.engine
        cleanupdb_onSetup(self.engine)

    def tearDown(self):
        cleanupdb_onTearDown(self.engine)

    def sql(self, *args, **kwargs):
        return self.engine.execute(*args, **kwargs)

    # Test: exam statistics for the periods:
    # last 2 days, last week, 3 weeks (starting from last week).
    def test_stat(self):
        create_exams(self)
        info = self.core._UserMixin__getExamStat(1, 1)

        # recent: 4 passed, 2 in progress, 2 failed (total 8).
        # err = 2 failed / (8 - 2 inprogress) = 2 / 6 = 33%
        self.assertEqual(info['current'], 33)

        # week: 7 in progress, 12 failed (total exams 28).
        # err = 12 / (20 - 7) = 12 / 21 = 57%
        self.assertEqual(info['week'], 57)

        # 3 weeks: 5 errors, 1 in progress, the rest are passed (total 21).
        # err = 5 / (21 - 1) = 5 / 20 = 25%
        self.assertEqual(info['week3'], 25)

    # Test: exam list for the periods (see above).
    def test_list(self):
        current, week, week3 = create_exams(self)
        info = self.core.getExamList(1, 1)
        exams = info['exams']
        self.assertIn('current', exams)
        self.assertIn('week', exams)
        self.assertIn('week3', exams)

        self.assertEqual(len(current), len(exams['current']))
        self.assertEqual(len(week), len(exams['week']))
        self.assertEqual(len(week3), len(exams['week3']))

        for x, y in zip(exams['current'], current):
            self.assertEqual(y, x['start'].split(' ')[0])

        for x, y in zip(exams['week'], week):
            self.assertEqual(y, x['start'].split(' ')[0])

        for x, y in zip(exams['week3'], week3):
            self.assertEqual(y, x['start'].split(' ')[0])

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ExamStatTest))
    return suite

if __name__ == '__main__':
    unittest.main()
