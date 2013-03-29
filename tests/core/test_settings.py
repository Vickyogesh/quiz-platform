# to use tests_common and quiz module
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))


import unittest
import hashlib
from quiz.settings import Settings


class CoreSettingsTest(unittest.TestCase):
    def setUp(self):
        Settings.CONFIG_FILE = 'config.ini'
        self.path = os.path.join(os.path.dirname(__file__), '..', 'data')

    def test_session(self):
        settings = Settings([self.path], verbose=False)

        info = settings.session
        self.assertEqual('file', info['session.type'])
        self.assertEqual('QUIZSID', info['session.key'])
        self.assertEqual('4e50d30', info['session.secret'])
        # TODO: test me
        # self.assertEqual('False', info['session.data_dir'])
        # self.assertEqual('False', info['session.lock_dir'])

    def test_dbinfo(self):
        settings = Settings([self.path], verbose=False)

        info = settings.dbinfo
        self.assertEqual('mysql://quiz:quiz@192.168.56.101', info['uri'])
        self.assertEqual('False', info['verbose'])
        self.assertEqual('quiz', info['dbname'])
        self.assertEqual('charset=utf8', info['params'])
        self.assertEqual('mysql://quiz:quiz@192.168.56.101/quiz?charset=utf8',
            info['database'])

        # test URI without trailing slash and params
        Settings.CONFIG_FILE = 'config2.ini'
        settings = Settings([self.path], verbose=False)
        info = settings.dbinfo
        self.assertEqual('mysql://quiz:quiz@192.168.56.101/', info['uri'])
        self.assertEqual('False', info['verbose'])
        self.assertEqual('quiz', info['dbname'])
        self.assertNotIn('params', info)
        self.assertEqual('mysql://quiz:quiz@192.168.56.101/quiz',
                         info['database'])

    def test_dbinfoEnv(self):
        os.environ['SOMEVAR'] = 'mysql://root:123@127.8.6.1:3342/'
        Settings.CONFIG_FILE = 'config3.ini'
        settings = Settings([self.path], verbose=False)
        info = settings.dbinfo
        self.assertEqual('mysql://root:123@127.8.6.1:3342/', info['uri'])
        self.assertEqual('False', info['verbose'])
        self.assertEqual('quiz', info['dbname'])
        self.assertEqual('mysql://root:123@127.8.6.1:3342/quiz',
                         info['database'])

    def test_sessionEnv(self):
        os.environ['DATA_DIR'] = '/tmp/data'
        Settings.CONFIG_FILE = 'config3.ini'
        settings = Settings([self.path], verbose=False)

        info = settings.session
        self.assertEqual('file', info['session.type'])
        self.assertEqual('QUIZSID', info['session.key'])
        self.assertEqual('4e50d30', info['session.secret'])
        self.assertEqual('/tmp/data/sessions/data', info['session.data_dir'])
        self.assertEqual('/tmp/data/sessions/lock', info['session.lock_dir'])

    def test_main(self):
        Settings.CONFIG_FILE = 'config3.ini'
        settings = Settings([self.path], verbose=False)
        main = settings.main

        m = hashlib.md5()
        m.update('admin:ari09Xsw_')
        self.assertEqual(m.hexdigest(), main['admin_password'])
        self.assertEqual(10, main['guest_allowed_requests'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(CoreSettingsTest))
    return suite

if __name__ == '__main__':
    unittest.main()
