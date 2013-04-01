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

    TEST_SCHOOLS = [
        {
            'name': 'Chuck Norris School',
            'login': 'chuck@norris.com',
            'passwd': 'boo'
        },
        {
            'name': 'School2',
            'login': 'school2',
            'passwd': 'boo'
        }
    ]
    TEST_USERS = [
        {
            'name': 'Test2',
            'surname': 'User2',
            'login': 'testuser2',
            'passwd': 'testpasswd2',
            'type': 'student',
            'school_id': 1
        },
        {
            'name': 'Test',
            'surname': 'User',
            'login': 'testuser',
            'passwd': 'testpasswd',
            'type': 'student',
            'school_id': 1
        }]

    def __init__(self, verbose=False, create_db=False, cfg_path=None):
        self.start_time = time.time()
        self._verbose = verbose
        self._readSettints(cfg_path)
        self._setup(create_db)
        self.put_users = False

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

    def _setupTables(self):
        print('Setup tables...')
        self._removeTables()
        self._createTables()
        self._createFuncs()

    def _removeTables(self):
        print('Removing tables...')
        metadata = MetaData(bind=self.engine)
        metadata.reflect()
        metadata.drop_all()

    def _createTables(self):
        print('Creating tables...')
        self.conn.execute(text(
            """ CREATE TABLE applications(
                id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
                appkey VARCHAR(50) NOT NULL,
                description VARCHAR(100),
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE schools(
                id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                login VARCHAR(100) NOT NULL,
                passwd VARCHAR(100) NOT NULL,
                CONSTRAINT PRIMARY KEY (id),
                CONSTRAINT UNIQUE (login)
            );

            CREATE TABLE users(
                id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
                name VARCHAR(100) NOT NULL,
                surname VARCHAR(100) NOT NULL,
                login VARCHAR(100) NOT NULL,
                passwd VARCHAR(100) NOT NULL,
                type ENUM('student', 'guest') NOT NULL,
                school_id INTEGER UNSIGNED NOT NULL,
                last_visit TIMESTAMP NOT NULL DEFAULT 0,
                CONSTRAINT PRIMARY KEY (id, school_id)
            );

            CREATE TABLE guest_access(
                id INTEGER UNSIGNED NOT NULL,
                num_requests SMALLINT UNSIGNED NOT NULL DEFAULT 0,
                period_end DATETIME NOT NULL,
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
                text VARCHAR(500) NOT NULL,
                text_fr VARCHAR(500),
                text_de VARCHAR(500),
                answer BOOLEAN NOT NULL,
                image VARCHAR(10),
                image_part VARCHAR(10),
                chapter_id SMALLINT UNSIGNED NOT NULL,
                topic_id INTEGER UNSIGNED NOT NULL,
                CONSTRAINT PRIMARY KEY (id)
            );

            CREATE TABLE topics_stat(
                user_id INTEGER UNSIGNED NOT NULL,
                topic_id INTEGER UNSIGNED NOT NULL,
                err_count SMALLINT NOT NULL DEFAULT 0
            );

            CREATE TABLE errors(
                user_id INTEGER UNSIGNED NOT NULL,
                question_id INTEGER UNSIGNED NOT NULL
            );

            CREATE TABLE quiz_answers(
                user_id INTEGER UNSIGNED NOT NULL,
                question_id INTEGER UNSIGNED NOT NULL,
                is_correct BOOLEAN NOT NULL DEFAULT FALSE
            );

            CREATE TABLE exam_answers(
                exam_id INTEGER UNSIGNED NOT NULL,
                question_id INTEGER UNSIGNED NOT NULL,
                is_correct BOOLEAN NOT NULL DEFAULT FALSE
            );

            CREATE TABLE exams(
                id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
                user_id INTEGER UNSIGNED NOT NULL,
                start_time DATETIME NOT NULL,
                end_time DATETIME DEFAULT NULL,
                err_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
                CONSTRAINT PRIMARY KEY (id)
            );
            """))

        self.meta = MetaData()
        self.meta.reflect(bind=self.engine)
        self.tbl_apps = self.meta.tables['applications']
        self.tbl_users = self.meta.tables['users']
        self.tbl_schools = self.meta.tables['schools']
        self.tbl_chapters = self.meta.tables['chapters']
        self.tbl_topics = self.meta.tables['topics']
        self.tbl_questions = self.meta.tables['questions']

    def _createFuncs(self):
        print('Creating function...')

        ### Delete users

        self.conn.execute("DROP TRIGGER IF EXISTS on_del_school;")
        self.conn.execute(text("""CREATE TRIGGER on_del_school
            BEFORE DELETE ON schools FOR EACH ROW
            DELETE FROM users WHERE school_id=OLD.id;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS on_del_user;")
        self.conn.execute(text("""CREATE TRIGGER on_del_user
            BEFORE DELETE ON users FOR EACH ROW BEGIN
                DELETE FROM errors WHERE user_id=OLD.id;
                DELETE FROM quiz_answers WHERE user_id=OLD.id;
                DELETE FROM exams WHERE user_id=OLD.id;
                DELETE FROM topics_stat WHERE user_id=OLD.id;
                IF OLD.type = 'guest' THEN
                    DELETE FROM guest_access WHERE id=OLD.id;
                END IF;
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS on_del_exam;")
        self.conn.execute(text("""CREATE TRIGGER on_del_exam
            BEFORE DELETE ON exams FOR EACH ROW
            DELETE FROM exam_answers WHERE exam_id=OLD.id;
            """))

        ### Logic

        self.conn.execute("DROP TRIGGER IF EXISTS add_guest;")
        self.conn.execute(text("""
            CREATE TRIGGER add_guest AFTER INSERT ON schools FOR EACH
            ROW INSERT IGNORE INTO users
                (name, surname, login, passwd, type, school_id) VALUES
                (NEW.name, '', CONCAT(NEW.login, '-guest'),
                 MD5(CONCAT(NEW.login, '-guest:guest')), 'guest', NEW.id);
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS guestaccess_add;")
        self.conn.execute(text("""
            CREATE TRIGGER guestaccess_add AFTER INSERT ON users FOR EACH
            ROW BEGIN
                IF NEW.type = 'guest' THEN
                    INSERT IGNORE INTO guest_access VALUES(NEW.id, 0,
                        UTC_TIMESTAMP()+ interval 1 hour);
                END IF;
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS guestaccess_update;")
        self.conn.execute(text("""
            CREATE TRIGGER guestaccess_update AFTER UPDATE ON users FOR EACH
            ROW BEGIN
                IF NEW.type = 'guest' THEN
                    UPDATE guest_access SET num_requests = num_requests + 1
                    WHERE id=NEW.id;
                END IF;
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS update_err_quiz;")
        self.conn.execute(text("""
            CREATE TRIGGER update_err_quiz AFTER INSERT ON quiz_answers FOR EACH
            ROW BEGIN
                IF NEW.is_correct = 0 THEN
                    INSERT IGNORE INTO errors VALUES(NEW.user_id, NEW.question_id);
                END IF;
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS update_err_examadd;")
        self.conn.execute(text("""
            CREATE TRIGGER update_err_examadd AFTER INSERT ON exam_answers FOR EACH
            ROW BEGIN
                DECLARE user INT UNSIGNED;
                SELECT user_id INTO user FROM exams WHERE id=NEW.exam_id;
                INSERT IGNORE INTO errors VALUES(user, NEW.question_id);
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS update_topic_stat_add;")
        self.conn.execute(text("""
            CREATE TRIGGER update_topic_stat_add AFTER INSERT ON errors FOR EACH
            ROW BEGIN
                DECLARE topic INT UNSIGNED;
                SELECT topic_id INTO topic FROM questions WHERE id=NEW.question_id;
                INSERT INTO topics_stat VALUES(NEW.user_id, topic, 1)
                ON DUPLICATE KEY UPDATE err_count = err_count + 1;
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS update_topic_stat_del;")
        self.conn.execute(text("""
            CREATE TRIGGER update_topic_stat_del AFTER DELETE ON errors FOR EACH
            ROW BEGIN
                DECLARE topic INT UNSIGNED;
                SELECT topic_id INTO topic FROM questions WHERE id=OLD.question_id;
                INSERT INTO topics_stat VALUES(OLD.user_id, topic, 0)
                ON DUPLICATE KEY UPDATE err_count = err_count - 1;
            END;
            """))

        self.conn.execute("DROP TRIGGER IF EXISTS update_err_exam;")
        self.conn.execute(text("""
            CREATE TRIGGER update_err_exam AFTER UPDATE ON exam_answers FOR EACH
            ROW BEGIN
                DECLARE user INT UNSIGNED;
                SELECT user_id INTO user FROM exams WHERE id=NEW.exam_id;

                IF NEW.is_correct = 1 THEN
                    DELETE FROM errors WHERE user_id=user
                    AND question_id=NEW.question_id;
                ELSE
                    INSERT IGNORE INTO errors VALUES(user, NEW.question_id);
                END IF;
            END;
            """))

    def _fillApps(self):
        print('Populating applications...')
        self.conn.execute(self.tbl_apps.insert(), DbTool.APPLICATIONS)

    def _create_digest(self, username, passwd):
        m = hashlib.md5()
        m.update('%s:%s' % (username, passwd))
        #print username, passwd, m.hexdigest()
        return m.hexdigest()

    def _fillUsers(self):
        if not self.put_users:
            return
        print("Populating users...")
        vals = []
        for user in DbTool.TEST_SCHOOLS:
            user['passwd'] = self._create_digest(user['login'], user['passwd'])
            vals.append(user)
        self.conn.execute(self.tbl_schools.insert(), vals)

        vals = []
        for user in DbTool.TEST_USERS:
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

        print("Creating indices... topics_stat")
        self.conn.execute('ALTER TABLE topics_stat ADD UNIQUE ix_topicstat(user_id, topic_id);')

        print("Creating indices... errors")
        self.conn.execute('ALTER TABLE errors ADD UNIQUE ix_errors(user_id, question_id);')

        print("Creating indices... quiz_answers")
        self.conn.execute('ALTER TABLE quiz_answers ADD UNIQUE ix_quiz_answers(user_id, question_id);')

        print("Creating indices... exams")
        self.conn.execute('ALTER TABLE exams ADD INDEX ix_exams(user_id);')

        print("Creating indices... exam_answers")
        self.conn.execute('ALTER TABLE exam_answers ADD UNIQUE ix_exam_answers(exam_id, question_id);')

        print("Doing tables optimizations...")
        self.conn.execute('OPTIMIZE TABLE applications;')
        self.conn.execute('OPTIMIZE TABLE chapters;')
        self.conn.execute('OPTIMIZE TABLE topics;')
        self.conn.execute('OPTIMIZE TABLE questions;')
        self.conn.execute('OPTIMIZE TABLE topics_stat;')
        self.conn.execute('OPTIMIZE TABLE errors;')
        self.conn.execute('OPTIMIZE TABLE quiz_answers;')
        self.conn.execute('OPTIMIZE TABLE exam_answers;')
        self.conn.execute('OPTIMIZE TABLE users;')
        self.conn.execute('OPTIMIZE TABLE schools;')
        self.conn.execute('OPTIMIZE TABLE guest_access;')

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
