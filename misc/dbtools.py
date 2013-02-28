import os
import os.path
import sys
import time

# to use settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))

import hashlib
from sqlalchemy import create_engine, MetaData, text
from quiz.settings import Settings


class DbTool(object):
    APPLICATIONS = [
        {
            'appkey': 'd1053fc29b0e07c7173890db4be19515bc04ae48',
            'description': 'mobileapp'
        },
        {
            'appkey': '32bfe1c505d4a2a042bafd53993f10ece3ccddca',
            'description': 'webapp'
        },
        {
            'appkey': 'b929d0c46cf5609e0104e50d301b0b8b482e9bfc',
            'description': 'desktopapp'
        }]

    REAL_USERS = [
        {
            'name': 'Admin',
            'login': 'root',
            'passwd': 'ari09Xsw_',
            'type': 'admin'
        }]

    TEST_USERS = [
        {
            'name': 'Test User',
            'login': 'testuser',
            'passwd': 'testpasswd',
            'type': 'student'
        },
        {
            'name': 'Admin',
            'login': 'root',
            'passwd': 'adminpwd',
            'type': 'admin'
        },
        {
            'name': 'Chuck Norris',
            'login': 'chuck@norris.com',
            'passwd': 'boo',
            'type': 'school'
        }]

    def __init__(self, verbose=False, create_db=False, cfg_path=None):
        self.start_time = time.time()
        self._users = DbTool.REAL_USERS
        self._verbose = verbose
        self._readSettints(cfg_path)
        self._setup(create_db)

    def _readSettints(self, path=None):
        if path is None:
            path = os.path.join(os.path.dirname(__file__),
                                '..',
                                'test-data',
                                'config.ini')
            paths = os.path.split(os.path.abspath(path))
        else:
            paths = os.path.split(path)

        Settings.CONFIG_FILE = paths[1]
        self.settings = Settings([paths[0]])

    def _setup(self, create_db):
        if create_db:
            print('Creating db...')
            engine = create_engine(self.settings.dbinfo['uri'],
                                   echo=self._verbose)
            engine.execute('CREATE DATABASE IF NOT EXISTS quiz;')

        print('Setup...')
        self.engine = create_engine(self.settings.dbinfo['database'],
                                    echo=self._verbose)
        self.conn = self.engine.connect()

    def _removeTables(self):
        print('Removing tables...')
        self.engine.execute('DROP TABLE IF EXISTS quiz_stat;')
        self.engine.execute('DROP TABLE IF EXISTS questions;')
        self.engine.execute('DROP TABLE IF EXISTS applications;')
        self.engine.execute('DROP TABLE IF EXISTS users;')
        self.engine.execute('DROP TABLE IF EXISTS topics;')
        self.engine.execute('DROP TABLE IF EXISTS chapters;')

    def _createTables(self):
        print('Creating tables...')
        self.conn.execute(text(
            """ CREATE TABLE applications(
                id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
                appkey VARCHAR(50) NOT NULL,
                description VARCHAR(100),
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE users(
                id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                login VARCHAR(100) NOT NULL,
                passwd VARCHAR(100) NOT NULL,
                type ENUM('admin', 'school', 'student', 'guest') NOT NULL,
                school_id INTEGER UNSIGNED,
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE chapters(
                id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
                priority TINYINT UNSIGNED NOT NULL,
                text VARCHAR(100) NOT NULL,
                min_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
                max_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE topics(
                id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
                text VARCHAR(200) NOT NULL,
                text_fr VARCHAR(200),
                text_de VARCHAR(200),
                chapter_id SMALLINT UNSIGNED,
                min_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
                max_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE questions(
                id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
                text VARCHAR(256) NOT NULL,
                text_fr VARCHAR(256),
                text_de VARCHAR(256),
                answer BOOLEAN NOT NULL,
                image VARCHAR(10),
                image_part VARCHAR(10),
                chapter_id SMALLINT UNSIGNED NOT NULL,
                topic_id INTEGER UNSIGNED NOT NULL,
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE quiz_stat(
                user_id INTEGER UNSIGNED NOT NULL,
                question_id INTEGER UNSIGNED NOT NULL
            );
            """))

        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)
        self.tbl_apps = self.meta.tables['applications']
        self.tbl_users = self.meta.tables['users']
        self.tbl_chapters = self.meta.tables['chapters']
        self.tbl_topics = self.meta.tables['topics']
        self.tbl_questions = self.meta.tables['questions']
        self.tbl_quizstat = self.meta.tables['quiz_stat']

    def _setupTables(self):
        print('Setup tables...')
        self._removeTables()
        self._createTables()

    def _fillApps(self):
        print('Populating applications...')
        self.conn.execute(self.tbl_apps.insert(), DbTool.APPLICATIONS)

    def _create_digest(self, username, passwd):
        m = hashlib.md5()
        m.update('%s:%s' % (username, passwd))
        return m.hexdigest()

    def _fillUsers(self):
        print("Populating users...")
        vals = []
        for user in self._users:
            user['passwd'] = self._create_digest(user['login'], user['passwd'])
            vals.append(user)
        self.conn.execute(self.tbl_users.insert(), vals)

    def _updateQuestionsStat(self):
        print("Updating questions stat...")
        self.conn.execute('DROP PROCEDURE IF EXISTS update_data_stat;')

        self.conn.execute("""CREATE PROCEDURE update_data_stat()
        BEGIN
        DECLARE done INT DEFAULT FALSE;
        DECLARE idval INTEGER UNSIGNED;
        DECLARE qmin_id INTEGER UNSIGNED;
        DECLARE qmax_id INTEGER UNSIGNED;

        DECLARE ch_cur CURSOR FOR
        SELECT c.id, q.mn, q.mx FROM chapters c
                     INNER JOIN (
                        SELECT chapter_id, min(id) mn, max(id) mx FROM questions
                        GROUP BY chapter_id
                     ) q ON c.id = q.chapter_id;

        DECLARE top_cur CURSOR FOR
        SELECT c.id, q.mn, q.mx FROM topics c
                     INNER JOIN (
                        SELECT topic_id, min(id) mn, max(id) mx FROM questions
                        GROUP BY topic_id
                     ) q ON c.id = q.topic_id;

        DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

        START TRANSACTION;
        OPEN ch_cur;
        ll: LOOP
            FETCH ch_cur INTO idval, qmin_id, qmax_id;
            IF done THEN
                LEAVE ll;
            END IF;
            UPDATE chapters SET min_id=qmin_id, max_id=qmax_id WHERE id=idval;
        END LOOP;
        CLOSE ch_cur;

        SET done = FALSE;
        OPEN top_cur;
        ll: LOOP
            FETCH top_cur INTO idval, qmin_id, qmax_id;
            IF done THEN
                LEAVE ll;
            END IF;
            UPDATE topics SET min_id=qmin_id, max_id=qmax_id WHERE id=idval;
        END LOOP;
        CLOSE top_cur;
        COMMIT;

        END;
        """)

        self.conn.execute('call update_data_stat();')
        self.conn.execute('DROP PROCEDURE IF EXISTS update_data_stat;')

    def _optimize(self):
        print("Creating indices... applications")
        self.conn.execute('ALTER TABLE applications ADD UNIQUE ix_app(appkey);')

        print("Creating indices... users")
        self.conn.execute('ALTER TABLE users ADD UNIQUE ix_login(login);')

        print("Creating indices... topics")
        self.conn.execute('ALTER TABLE topics ADD INDEX ix_chid(chapter_id);')

        print("Creating indices... questions")
        self.conn.execute('ALTER TABLE questions ADD INDEX ix_tp(topic_id);')
        self.conn.execute('ALTER TABLE questions ADD INDEX ix_ch(chapter_id);')

        print("Creating indices... quiz_stat")
        self.conn.execute('ALTER TABLE quiz_stat ADD UNIQUE ix_quiz(question_id, user_id);')

        print("Doing tables optimizations...")
        self.conn.execute('OPTIMIZE TABLE applications, users, chapters;')
        self.conn.execute('OPTIMIZE TABLE topics;')
        self.conn.execute('OPTIMIZE TABLE questions;')
        self.conn.execute('OPTIMIZE TABLE quiz_stat;')

    def before(self):
        pass

    def fillData(self):
        pass

    def after(self):
        pass

    def run(self):
        t = self.conn.begin()
        try:
            self.before()
            self._setupTables()
            self._fillApps()
            self._fillUsers()
            self.fillData()
            self._updateQuestionsStat()
            self._optimize()
            self.after()
        except Exception as e:
            print(e)
            print('Rollback changes...')
            t.rollback()
        except:
            print('Rollback changes...')
            t.rollback()
        else:
            t.commit()
        print('Finished in ~{0:.2f}s'.format(time.time() - self.start_time))
