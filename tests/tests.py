import argparse
import unittest

suite = unittest.TestSuite()

parser = argparse.ArgumentParser(description='Quiz web service tests runner')
parser.add_argument('-t', '--tests',
                    help='Tests to run (by default run http)',
                    choices=['core', 'http'],
                    default=['http'])
args = parser.parse_args()

if 'core' in args.tests:
    import core.test_db
    import core.test_quizsettings
    suite.addTest(core.test_db.suite())
    suite.addTest(core.test_quizsettings.suite())

if 'http' in args.tests:
    import http.test_auth
    import http.test_quiz
    suite.addTest(http.test_auth.suite())
    suite.addTest(http.test_quiz.suite())

unittest.TextTestRunner(verbosity=2).run(suite)
