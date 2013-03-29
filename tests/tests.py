import argparse
import unittest
import imp
import os


def all_tests(dest, tests_path):
    path = os.path.dirname(__file__)
    path = os.path.join(path, tests_path)
    base, _, files = os.walk(path).next()
    for f in files:
        fname = os.path.join(base, f)
        info = os.path.basename(f).split('.')
        if info[1] != 'py':
            continue
        try:
            mod = imp.load_source(info[0], fname)
            dest.addTest(mod.suite())
        except Exception:
            print "[SKIP] %s.%s" % (tests_path, info[0])


default_tests = ['core', 'http']
suite = unittest.TestSuite()

parser = argparse.ArgumentParser(description='Quiz WebService tests runner.')
parser.add_argument('-t', '--tests',
                    help='Test to run (by default run all tests).',
                    choices=default_tests,
                    action='append')
parser.add_argument('-v', '--verbosity', type=int, default=1, metavar='NUM',
                    help='Output verbosity level (default: %(default)s)')

args = parser.parse_args()
if not args.tests:
    args.tests = default_tests
for p in args.tests:
    all_tests(suite, p)

unittest.TextTestRunner(verbosity=args.verbosity).run(suite)
