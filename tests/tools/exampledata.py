from sqlalchemy import text
import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))
import random
from quiz.core.core import QuizCore
from sqlalchemy import MetaData

users = [
    {
        'login': 'studente',
        'name': 'Test',
        'sname': 'Studente'
    },
    {
        'login': 'vandamme@mail.com',
        'name': 'Jean-Claude',
        'sname': 'Van Damme'
    },
    {
        'login': 'willis@mail.com',
        'name': 'Bruce',
        'sname': 'Willis'
    }
]
sid = -1


def fill(mgr):
    print("Fill with example data ...")
    create_users(mgr)
    create_guestvisits(mgr)
    create_user_progress(mgr)
    create_school_topic_err_snapshot(mgr)
    create_topics_snapshots(mgr)
    create_exams(mgr)

    mgr.meta = MetaData()
    mgr.meta.reflect(bind=mgr.engine)

    for tbl in mgr.meta.tables:
        print("Table optimizations... %s" % tbl)
        mgr.conn.execute('OPTIMIZE TABLE %s;' % tbl)


def create_users(mgr):
    global users
    global sid
    print("Creating users...")
    engine = mgr.engine

    sid = 1
    # create guest student entry
    engine.execute("DELETE FROM users WHERE school_id=1")
    engine.execute("INSERT INTO users VALUES(1, 'guest', 3, 1, UTC_TIMESTAMP(), -1)")

    sql = text("INSERT INTO users VALUES(:id, 'student', 3, 1, UTC_TIMESTAMP(), -1)")
    for id in xrange(2, 5):
        engine.execute(sql, id=id)


def create_guestvisits(mgr):
    print("Create guest visits ...")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.engine.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE i INT DEFAULT 1;
            DECLARE numdays INT DEFAULT 35;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR select id from users where school_id=1 and quiz_type=1;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            SET dt = DATE(UTC_TIMESTAMP());
            OPEN cur;

            START TRANSACTION;
            rloop: LOOP
                FETCH cur INTO i;
                IF done THEN
                    LEAVE rloop;
                END IF;

                SET d = dt;
                WHILE (day <= numdays) DO
                    INSERT IGNORE INTO guest_access_snapshot
                    VALUES(i, 3, d, FLOOR(20 + (RAND() * 80)));

                    SET day = day + 1;
                    SET d = d - interval 1 day;
                END WHILE;
                SET day = 1;
            END LOOP;
            COMMIT;

            CLOSE cur;
        END;""")
    mgr.engine.execute("call tst()")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create uest visits ...done")


def create_exams(mgr):
    print("Create exams ...")
    core = QuizCore(mgr.settings)
    res = mgr.engine.execute("SELECT id FROM users WHERE type='student' and school_id=%d and quiz_type=3" % sid)
    for row in res:
        id = row[0]
        for z in xrange(4):
            info = core.createExam(3, id, 'it')
            answers = [random.randint(0, 1) for row in info['questions']]
            eid = info['exam']['id']
            q = [x['id'] for x in info['questions']]
            core.saveExam(eid, q, answers)
    print("Create exams ...done")
    print("Create quiz results ...")
    for topic in xrange(1, 8):
        for x in xrange(4):
            info = core.getQuiz(3, id, topic, 'it', False)
            q = [x['id'] for x in info['questions']]
            if not q:
                continue
            answers = [random.randint(0, 1) for row in info['questions']]
            core.saveQuiz(3, id, topic, q, answers)
    core = None


def create_user_progress(mgr):
    print("Create user progress ...")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.engine.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE numdays INT DEFAULT 35;
            DECLARE user INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT id FROM users WHERE type='student' and school_id=%d and quiz_type=3;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            PREPARE stmt FROM 'INSERT IGNORE INTO user_progress_snapshot VALUES(?, 3, ?, ?)';

            SET dt = DATE(UTC_TIMESTAMP());
            OPEN cur;

            START TRANSACTION;
            rloop: LOOP
                FETCH cur INTO user;
                IF done THEN
                    LEAVE rloop;
                END IF;

                SET d = dt;
                WHILE (day <= numdays) DO
                    SET @a = user;
                    SET @b = d;
                    SET @c = FLOOR(1 + (RAND() * 99)) / 100;
                    EXECUTE stmt USING @a, @b, @c;

                    SET day = day + 1;
                    SET d = d - interval 1 day;
                END WHILE;
                SET day = 1;
                SET user = user + 1;
            END LOOP;
            COMMIT;
            DEALLOCATE PREPARE stmt;
            CLOSE cur;
        END;""" % sid)
    mgr.engine.execute("call tst()")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create user progress ...done")


def create_school_topic_err_snapshot(mgr):
    print("Create schools topic_err snapshots ...")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.engine.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE numtopics INT DEFAULT 45;
            DECLARE numdays INT DEFAULT 35;
            DECLARE topic INT DEFAULT 1;
            DECLARE school INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE err FLOAT DEFAULT 0;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT {0};
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            PREPARE stmt FROM 'INSERT INTO school_topic_err_snapshot VALUES(?, 3, ?, ?, ?)';

            SET dt = DATE(UTC_TIMESTAMP());
            OPEN cur;

            DELETE FROM school_topic_err_snapshot WHERE school_id={0} and quiz_type=3;

            START TRANSACTION;
            rloop: LOOP
                FETCH cur INTO school;
                IF done THEN
                    LEAVE rloop;
                END IF;

                WHILE (topic <= numtopics) DO
                    SET d = dt;
                    WHILE (day <= numdays) DO
                        SET err = err + 0.5;
                        SET @a = school;
                        SET @b = topic;
                        SET @c = d;
                        SET @d = err;
                        EXECUTE stmt USING @a, @b, @c, @d;
                        SET day = day + 1;
                        SET d = d - interval 1 day;
                    END WHILE;
                    SET day = 1;
                    SET err = 0;
                    SET topic = topic + 1;
                END WHILE;
                SET topic = 1;
            END LOOP;
            COMMIT;

            DEALLOCATE PREPARE stmt;
            CLOSE cur;
        END;""".format(sid))
    mgr.engine.execute("call tst()")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create uest visits ...done")


def create_topics_snapshots(mgr):
    print("Create topics snapshots ...")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.engine.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE numtopics INT DEFAULT 45;
            DECLARE numdays INT DEFAULT 35;
            DECLARE user INT DEFAULT 1;
            DECLARE topic INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;
            DECLARE err FLOAT DEFAULT 0;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT id FROM users WHERE type='student' and school_id=%d and quiz_type=3;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            PREPARE stmt FROM 'INSERT IGNORE INTO topic_err_snapshot VALUES(?, 3, ?, ?, ?)';
            PREPARE stmt1 FROM 'INSERT IGNORE INTO topic_err_current VALUES(?, 3, ?, ?, ?)';

            SET dt = DATE(UTC_TIMESTAMP());
            OPEN cur;

            START TRANSACTION;
            rloop: LOOP
                FETCH cur INTO user;
                IF done THEN
                    LEAVE rloop;
                END IF;

                WHILE (topic <= numtopics) DO
                    SET d = dt;
                    WHILE (day <= numdays) DO
                        SET err = err + 0.5;
                        SET @a = user;
                        SET @b = topic;
                        SET @c = d;
                        SET @d = err;
                        EXECUTE stmt USING @a, @b, @c, @d;
                        SET day = day + 1;
                        SET d = d - interval 1 day;
                    END WHILE;
                    SET day = 1;
                    SET err = 0;
                    SET topic = topic + 1;
                    SET @c = 20;
                    SET @d = 60;
                    EXECUTE stmt1 USING @a, @b, @c, @d;
                END WHILE;
                SET topic = 1;
            END LOOP;
            COMMIT;
            DEALLOCATE PREPARE stmt;
            DEALLOCATE PREPARE stmt1;
            CLOSE cur;
        END;""" % sid)
    mgr.engine.execute("call tst()")
    mgr.engine.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create topics snapshots ...done")
