from sqlalchemy import MetaData


def recreate(mgr, recreate=True):
    if recreate:
        print('Recreating tables...')
        remove(mgr)
        create(mgr)
        print('Recreating tables... done')
    else:
        reflect(mgr)


def optimize(mgr):
    create_indices(mgr)
    do_optimize(mgr)


def remove(mgr):
    metadata = MetaData(bind=mgr.engine)
    metadata.reflect()
    metadata.drop_all()


# NOTE: quiz_type = 0 - QuizB related data
def create(mgr):
    mgr.conn.execute("""CREATE TABLE applications(
            id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
            appkey VARCHAR(50) NOT NULL,
            description VARCHAR(100),
            CONSTRAINT PRIMARY KEY (id)
        );


        CREATE TABLE school_topic_err(
            school_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            topic_id INTEGER UNSIGNED NOT NULL,
            err_count SMALLINT NOT NULL DEFAULT 0,
            count SMALLINT NOT NULL DEFAULT 0,
            err_week FLOAT NOT NULL DEFAULT -1,
            err_week3 FLOAT NOT NULL DEFAULT -1,
            CONSTRAINT PRIMARY KEY (school_id, quiz_type, topic_id)
        );
        CREATE TABLE school_topic_err_snapshot(
            school_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            topic_id INTEGER UNSIGNED NOT NULL,
            now_date DATE NOT NULL,
            err_percent FLOAT NOT NULL DEFAULT -1,
            CONSTRAINT PRIMARY KEY (school_id, quiz_type, topic_id, now_date)
        );
        CREATE TABLE school_stat_cache(
            school_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            last_activity DATETIME NOT NULL DEFAULT 0,
            last_update DATETIME NOT NULL DEFAULT 0,
            stat_cache TEXT NOT NULL,
            CONSTRAINT PRIMARY KEY (school_id, quiz_type)
        );

        CREATE TABLE stat_json(
            name VARCHAR(80) NOT NULL,
            value TEXT NOT NULL,
            CONSTRAINT PRIMARY KEY (name)
        );

        CREATE TABLE guest_access(
            id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            num_requests SMALLINT UNSIGNED NOT NULL DEFAULT 0,
            period_end DATETIME NOT NULL,
            CONSTRAINT PRIMARY KEY (id, quiz_type)
        );
        CREATE TABLE guest_access_snapshot(
            guest_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            now_date DATE NOT NULL,
            num_requests SMALLINT UNSIGNED NOT NULL DEFAULT 0,
            CONSTRAINT PRIMARY KEY (guest_id, quiz_type, now_date)
        );


        CREATE TABLE users(
            id INTEGER UNSIGNED NOT NULL,
            type ENUM('student', 'guest') NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            school_id INTEGER UNSIGNED NOT NULL,
            last_visit TIMESTAMP NOT NULL DEFAULT 0,
            progress_coef FLOAT NOT NULL DEFAULT -1,
            CONSTRAINT PRIMARY KEY (id, quiz_type, school_id)
        );
        CREATE TABLE user_progress_snapshot(
            user_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            now_date DATE NOT NULL,
            progress_coef FLOAT NOT NULL DEFAULT -1,
            CONSTRAINT PRIMARY KEY (user_id, quiz_type, now_date)
        );


        CREATE TABLE chapters(
            id SMALLINT UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            priority TINYINT UNSIGNED NOT NULL,
            text VARCHAR(100) NOT NULL,
            min_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
            max_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
            CONSTRAINT PRIMARY KEY (id, quiz_type)
        );
        CREATE TABLE topics(
            id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            text VARCHAR(200) NOT NULL,
            text_fr VARCHAR(200),
            text_de VARCHAR(200),
            chapter_id SMALLINT UNSIGNED,
            min_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
            max_id INTEGER UNSIGNED NOT NULL DEFAULT 0,
            CONSTRAINT PRIMARY KEY (id, quiz_type)
        );
        CREATE TABLE questions(
            id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            text VARCHAR(500) NOT NULL,
            text_fr VARCHAR(500),
            text_de VARCHAR(500),
            answer BOOLEAN NOT NULL,
            image VARCHAR(10),
            image_part VARCHAR(10),
            chapter_id SMALLINT UNSIGNED NOT NULL,
            topic_id INTEGER UNSIGNED NOT NULL,
            CONSTRAINT PRIMARY KEY (id, quiz_type)
        );

        CREATE TABLE blacklist(
            id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            CONSTRAINT PRIMARY KEY (id, quiz_type)
        );


        CREATE TABLE topic_err_current(
            user_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            topic_id INTEGER UNSIGNED NOT NULL,
            err_count SMALLINT NOT NULL DEFAULT 0,
            count SMALLINT NOT NULL DEFAULT 0,
            CONSTRAINT PRIMARY KEY (user_id, quiz_type, topic_id)
        );
        CREATE TABLE topic_err_snapshot(
            user_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            topic_id INTEGER UNSIGNED NOT NULL,
            now_date DATE NOT NULL,
            err_percent FLOAT NOT NULL DEFAULT -1,
            CONSTRAINT PRIMARY KEY (user_id, quiz_type, topic_id, now_date)
        );


        CREATE TABLE answers(
            user_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            question_id INTEGER UNSIGNED NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT PRIMARY KEY (user_id, quiz_type, question_id)
        );
        CREATE TABLE quiz_answers(
            user_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            question_id INTEGER UNSIGNED NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT PRIMARY KEY (user_id, quiz_type, question_id)
        );
        CREATE TABLE exam_answers(
            add_id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
            exam_id INTEGER UNSIGNED NOT NULL,
            question_id INTEGER UNSIGNED NOT NULL,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            is_correct BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT PRIMARY KEY (add_id)
        );


        CREATE TABLE exams(
            id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
            quiz_type SMALLINT UNSIGNED NOT NULL,
            user_id INTEGER UNSIGNED NOT NULL,
            start_time DATETIME NOT NULL,
            end_time DATETIME DEFAULT NULL,
            err_count SMALLINT UNSIGNED NOT NULL DEFAULT 0,
            CONSTRAINT PRIMARY KEY (id, quiz_type)
        );

        CREATE TABLE truck_last_sublicense(
          user_id INTEGER UNSIGNED NOT NULL,
          user_type SMALLINT UNSIGNED NOT NULL,
          sublicense SMALLINT UNSIGNED NOT NULL,
          CONSTRAINT PRIMARY KEY (user_id, user_type)
        );
        """)
    reflect(mgr)


def reflect(mgr):
    mgr.meta = MetaData()
    mgr.meta.reflect(bind=mgr.engine)
    mgr.tbl_apps = mgr.meta.tables['applications']
    mgr.tbl_users = mgr.meta.tables['users']
    mgr.tbl_chapters = mgr.meta.tables['chapters']
    mgr.tbl_topics = mgr.meta.tables['topics']
    mgr.tbl_questions = mgr.meta.tables['questions']


def create_indices(mgr):
    print("Creating indices... applications")
    try:
        mgr.engine.execute('DROP INDEX ix_app ON applications')
        mgr.engine.execute('DROP INDEX ix_chid ON topics')
        mgr.engine.execute('DROP INDEX ix_tp ON questions')
        mgr.engine.execute('DROP INDEX ix_ch ON questions')
        mgr.engine.execute('DROP INDEX ix_exams ON exams')
        mgr.engine.execute('DROP INDEX ix_exam_answers ON exam_answers')
    except:
        pass
    mgr.conn.execute('ALTER TABLE applications ADD UNIQUE ix_app(appkey);')

    print("Creating indices... topics")
    mgr.conn.execute('ALTER TABLE topics ADD INDEX ix_chid(chapter_id);')

    print("Creating indices... questions")
    mgr.conn.execute('ALTER TABLE questions ADD INDEX ix_tp(topic_id);')
    mgr.conn.execute('ALTER TABLE questions ADD INDEX ix_ch(chapter_id);')

    print("Creating indices... exams")
    mgr.conn.execute('ALTER TABLE exams ADD INDEX ix_exams(user_id);')
    mgr.conn.execute('ALTER TABLE exam_answers ADD UNIQUE ix_exam_answers(exam_id, question_id, quiz_type)')


def do_optimize(mgr):
    pass
    # for tbl in mgr.meta.tables:
    #     print("Table optimizations... %s" % tbl)
    #     mgr.conn.execute('OPTIMIZE TABLE %s;' % tbl)
