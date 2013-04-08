from sqlalchemy import text

func_list = []


def add_me(func):
    global func_list
    func_list.append(func)
    return func


def create(mgr):
    for func in func_list:
        print('Creating db triggers and procedures... %s' % func.__name__)
        func(mgr)


@add_me
def answers(mgr):
    # If new answer is added then update number of
    # errors and answers of the topic in the
    # topic_err_current table for then current date.
    # If there is no such row in the topic_err_current then
    # create it and set number of answers to 1.
    # Otherwise, increase number of answers and update
    # number of errors.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_answer_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_answer_add
        AFTER INSERT ON answers FOR EACH ROW BEGIN
            DECLARE topic INTEGER UNSIGNED;
            DECLARE err SMALLINT DEFAULT 0;

            SELECT topic_id INTO topic FROM questions
            WHERE id=NEW.question_id;

            IF NEW.is_correct = 0 THEN
                SET err=1;
            END IF;

            INSERT INTO topic_err_current
            (user_id, topic_id, now_date, err_count, count) VALUES
            (NEW.user_id, topic, DATE(UTC_TIMESTAMP()), err, 1)
            ON DUPLICATE KEY UPDATE now_date=VALUES(now_date),
            err_count=err_count+VALUES(err_count),
            count=count+VALUES(count);
        END;
        """))

    # If answer is changed then update number of errors and current date,
    # in the topic_err_current table. If there is no row in the
    # topic_err_current then add it and set number of answers to 1.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_answer_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_answer_upd
        AFTER UPDATE ON answers FOR EACH ROW BEGIN
            DECLARE topic INTEGER UNSIGNED;
            DECLARE err SMALLINT DEFAULT -1;

            IF OLD.is_correct != NEW.is_correct THEN
                SELECT topic_id INTO topic FROM questions
                WHERE id=NEW.question_id;

                IF NEW.is_correct = 0 THEN
                    SET err=1;
                END IF;

                INSERT INTO topic_err_current
                (user_id, topic_id, now_date, err_count, count) VALUES
                (NEW.user_id, topic, DATE(UTC_TIMESTAMP()), err, 1)
                ON DUPLICATE KEY UPDATE now_date=VALUES(now_date),
                err_count=err_count+VALUES(err_count);
            END IF;
        END;
        """))


@add_me
def topic_err_current(mgr):
    # If new entry is added to the topic_err_current table then
    # before inserting calc week and month columns by getting
    # errors percent for the last week and last month
    # from the topic_err_snapshot table; and also insert (or update)
    # snapshot of the current state to the topic_err_snapshot table.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_topic_err_current_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_topic_err_current_add
        BEFORE INSERT ON topic_err_current FOR EACH ROW BEGIN
            DECLARE week FLOAT DEFAULT -1;
            DECLARE month FLOAT DEFAULT -1;

            SELECT err_percent INTO week FROM topic_err_snapshot
            WHERE user_id=NEW.user_id AND topic_id=NEW.topic_id
            AND now_date >= NEW.now_date - interval 1 week
            ORDER BY now_date LIMIT 1;

            SELECT err_percent INTO month FROM topic_err_snapshot
            WHERE user_id=NEW.user_id AND topic_id=NEW.topic_id
            AND now_date >= NEW.now_date - interval 1 month
            ORDER BY now_date LIMIT 1;

            SET NEW.week = week;
            SET NEW.month = month;

            INSERT INTO topic_err_snapshot VALUES
            (NEW.user_id, NEW.topic_id, NEW.now_date,
             NEW.err_count/NEW.count*100)
            ON DUPLICATE KEY UPDATE err_percent=VALUES(err_percent);
        END;
        """))

    # Before update if date is changed recalc week and month columns
    # and update snapshot of the current state.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_topic_err_current_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_topic_err_current_upd
        BEFORE UPDATE ON topic_err_current FOR EACH ROW BEGIN
            DECLARE week FLOAT DEFAULT -1;
            DECLARE month FLOAT DEFAULT -1;

            IF NEW.now_date != OLD.now_date THEN
                SELECT err_percent INTO week FROM topic_err_snapshot
                WHERE user_id=NEW.user_id AND topic_id=NEW.topic_id
                AND now_date >= NEW.now_date - interval 1 week
                ORDER BY now_date LIMIT 1;

                SELECT err_percent INTO month FROM topic_err_snapshot
                WHERE user_id=NEW.user_id AND topic_id=NEW.topic_id
                AND now_date >= NEW.now_date - interval 1 month
                ORDER BY now_date LIMIT 1;

                SET NEW.week = week;
                SET NEW.month = month;
            END IF;

            INSERT INTO topic_err_snapshot VALUES
            (NEW.user_id, NEW.topic_id, NEW.now_date,
             NEW.err_count/NEW.count*100)
            ON DUPLICATE KEY UPDATE err_percent=VALUES(err_percent);
        END;
        """))


@add_me
def delete_users(mgr):
    # Delete all school's students.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_del_school;")
    mgr.conn.execute(text("""CREATE TRIGGER on_del_school
        BEFORE DELETE ON schools FOR EACH ROW
        DELETE FROM users WHERE school_id=OLD.id;
        """))

    # Before delete a user we delete all user's data.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_del_user;")
    mgr.conn.execute(text("""CREATE TRIGGER on_del_user
        BEFORE DELETE ON users FOR EACH ROW BEGIN
            DELETE FROM topic_err_snapshot WHERE user_id=OLD.id;
            DELETE FROM answers WHERE user_id=OLD.id;
            DELETE FROM quiz_answers WHERE user_id=OLD.id;
            DELETE FROM exams WHERE user_id=OLD.id;
            DELETE FROM topic_err_current WHERE user_id=OLD.id;
            DELETE FROM topic_err_snapshot WHERE user_id=OLD.id;
            IF OLD.type = 'guest' THEN
                DELETE FROM guest_access WHERE id=OLD.id;
            END IF;
        END;
        """))

    # Before delete exam we delete exam's answers.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_del_exam;")
    mgr.conn.execute(text("""CREATE TRIGGER on_del_exam
        BEFORE DELETE ON exams FOR EACH ROW
        DELETE FROM exam_answers WHERE exam_id=OLD.id;
        """))


@add_me
def guest(mgr):
    # If school is added then we create school's guest user.
    mgr.conn.execute("DROP TRIGGER IF EXISTS add_guest;")
    mgr.conn.execute(text("""CREATE TRIGGER add_guest
        AFTER INSERT ON schools FOR EACH ROW
        INSERT IGNORE INTO users
            (name, surname, login, passwd, type, school_id) VALUES
            (NEW.name, '', CONCAT(NEW.login, '-guest'),
             MD5(CONCAT(NEW.login, '-guest:guest')), 'guest', NEW.id);
        """))

    # If guest is added then we update guest access info.
    mgr.conn.execute("DROP TRIGGER IF EXISTS guestaccess_add;")
    mgr.conn.execute(text("""CREATE TRIGGER guestaccess_add
        AFTER INSERT ON users FOR EACH ROW
        BEGIN
            IF NEW.type = 'guest' THEN
                INSERT IGNORE INTO guest_access VALUES(NEW.id, 0,
                    UTC_TIMESTAMP()+ interval 1 hour);
            END IF;
        END;
        """))

    # If user activity timestamp is changed and if user is guest
    # then we update number of requests.
    mgr.conn.execute("DROP TRIGGER IF EXISTS guestaccess_update;")
    mgr.conn.execute(text("""CREATE TRIGGER guestaccess_update
        AFTER UPDATE ON users FOR EACH ROW
        BEGIN
            IF NEW.type = 'guest' THEN
                UPDATE guest_access SET num_requests = num_requests + 1
                WHERE id=NEW.id;
            END IF;
        END;
        """))


@add_me
def quiz_answers(mgr):
    mgr.conn.execute("DROP PROCEDURE IF EXISTS upd_answer;")
    mgr.conn.execute(text("""CREATE PROCEDURE upd_answer
        (IN user INTEGER UNSIGNED, IN quest INTEGER UNSIGNED, IN correct BOOLEAN)
        BEGIN
            INSERT INTO answers VALUES(user, quest, correct)
            ON DUPLICATE KEY UPDATE is_correct = VALUES(is_correct);
        END;
        """))

    mgr.conn.execute("DROP TRIGGER IF EXISTS quiz_add;")
    mgr.conn.execute(text("""CREATE TRIGGER quiz_add
        AFTER INSERT ON quiz_answers FOR EACH ROW
        CALL upd_answer(NEW.user_id, NEW.question_id, NEW.is_correct);
        """))

    mgr.conn.execute("DROP TRIGGER IF EXISTS quiz_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER quiz_upd
        AFTER UPDATE ON quiz_answers FOR EACH
        ROW CALL upd_answer(NEW.user_id, NEW.question_id, NEW.is_correct);
        """))


@add_me
def exam_answers(mgr):
    # mgr.conn.execute("DROP TRIGGER IF EXISTS exam_add;")
    # mgr.conn.execute(text("""CREATE TRIGGER exam_add
    #     AFTER INSERT ON exam_answers FOR EACH ROW BEGIN
    #         DECLARE user INT UNSIGNED;
    #         SELECT user_id INTO user FROM exams WHERE id=NEW.exam_id;
    #         CALL upd_answer(user, NEW.question_id, NEW.is_correct);
    #     END;
    #     """))

    mgr.conn.execute("DROP TRIGGER IF EXISTS exam_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER exam_upd
        BEFORE UPDATE ON exam_answers FOR EACH ROW BEGIN
            DECLARE user INT UNSIGNED;
            SELECT user_id INTO user FROM exams WHERE id=NEW.exam_id;
            CALL upd_answer(user, NEW.question_id, NEW.is_correct);
        END;
        """))
