import argparse
import unittest

default_tests = ['core', 'http']
suite = unittest.TestSuite()

parser = argparse.ArgumentParser(description='Quiz WebService tests runner.')
parser.add_argument('-t', '--tests',
                    help='Test to run (by default run all tests).',
                    choices=default_tests,
                    action='append')
args = parser.parse_args()

if not args.tests:
    args.tests = default_tests

if 'core' in args.tests:
    import core.test_settings
    import core.test_db_quiz
    import core.test_db_exam
    import core.test_db_review
    import core.test_db_topicstat
    suite.addTest(core.test_settings.suite())
    suite.addTest(core.test_db_quiz.suite())
    suite.addTest(core.test_db_exam.suite())
    suite.addTest(core.test_db_review.suite())
    suite.addTest(core.test_db_topicstat.suite())

if 'http' in args.tests:
    import http.test_auth
    import http.test_quiz
    suite.addTest(http.test_auth.suite())
    suite.addTest(http.test_quiz.suite())

unittest.TextTestRunner(verbosity=2).run(suite)
