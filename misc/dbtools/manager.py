import os
import os.path
import sys
import time
import hashlib

# to use settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

from sqlalchemy import create_engine
from quiz.settings import Settings
from . import tables, func, default_data, questions


class DbManager(object):
    def __init__(self, verbose=False, create_db=False, cfg_path=None):
        self.start_time = time.time()
        self._verbose = verbose
        self.__readSettints(cfg_path)
        self.__setup(create_db)
        self.put_users = False

    def __readSettints(self, path=None):
        if path is None:
            path = os.path.join(os.path.dirname(__file__),
                                '..',
                                '..',
                                'test-data',
                                'config.ini')
            paths = os.path.split(os.path.abspath(path))
        else:
            paths = os.path.split(path)

        Settings.CONFIG_FILE = paths[1]
        self.settings = Settings([paths[0]])

    def __setup(self, create_db):
        if create_db:
            print('Creating db...')
            engine = create_engine(self.settings.dbinfo['uri'],
                                   echo=self._verbose)
            engine.execute('CREATE DATABASE IF NOT EXISTS quiz;')

        print('Setup...')
        self.engine = create_engine(self.settings.dbinfo['database'],
                                    echo=self._verbose)
        self.conn = self.engine.connect()

    def _create_digest(self, username, passwd):
        m = hashlib.md5()
        m.update('%s:%s' % (username, passwd))
        return m.hexdigest()

    def before(self):
        pass

    def fillData(self):
        pass

    def after(self):
        pass

    def _do_run(self):
        self.before()
        tables.recreate(self)
        func.create(self)
        default_data.fill(self)
        self.fillData()
        questions.update_stat(self)
        tables.optimize(self)
        self.after()

    def run(self):
        t = self.conn.begin()
        msg = ''
        try:
            self._do_run()
        except Exception as e:
            print(e)
            print('Rollback changes...')
            msg = '[Interrupted] '
            t.rollback()
        except:
            print('Rollback changes...')
            msg = '[Interrupted] '
            t.rollback()
        else:
            t.commit()
        print('{0}Finished in ~{1:.2f}s'.format(msg, time.time() - self.start_time))