"""
This module contains function for attaching
triggers to the tables and for creating stored procedures.
"""
from sqlalchemy import text

# Functions to execute.
# See create().
func_list = []


# Helper decorator to include function to
# the list of functions (func_list) for execution.
# See create().
def add_me(func):
    global func_list
    func_list.append(func)
    return func


# Execute functions from the func_list.
# See add_me().
def create(mgr):
    for func in func_list:
        print('Creating db triggers and procedures... %s' % func.__name__)
        func(mgr)


@add_me
def answers(mgr):
    # If new answer is added then update number of
    # errors and answers of the topic in the
    # topic_err_current table for the current date.
    # If there is no such row in the topic_err_current then
    # create it and set number of answers to 1.
    # Otherwise, increase number of answers and update
    # number of errors.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_answer_after_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_answer_after_add
        AFTER INSERT ON answers FOR EACH ROW BEGIN
            DECLARE school INTEGER UNSIGNED DEFAULT NULL;
            DECLARE topic INTEGER UNSIGNED;
            DECLARE qtype INTEGER UNSIGNED;
            DECLARE err SMALLINT DEFAULT 0;

            SELECT school_id INTO school FROM users WHERE
            id=NEW.user_id AND type='student' AND quiz_type=NEW.quiz_type;

            SELECT topic_id, quiz_type INTO topic, qtype FROM questions
            WHERE id=NEW.question_id AND quiz_type=NEW.quiz_type;

            IF NEW.is_correct = 0 THEN
                SET err=1;
            END IF;

            INSERT INTO topic_err_current VALUES
            (NEW.user_id, qtype, topic, err, 1)
            ON DUPLICATE KEY UPDATE err_count=err_count+VALUES(err_count),
            count=count+VALUES(count);

            IF school IS NOT NULL THEN
                INSERT INTO school_topic_err
                (school_id, topic_id, quiz_type, err_count, count)
                VALUES (school, topic, qtype, err, 1) ON DUPLICATE KEY UPDATE
                err_count=err_count+VALUES(err_count),
                count=count+VALUES(count);
            END IF;
        END;
        """))

    # If answer is changed then update number of errors and current date,
    # in the topic_err_current table. If there is no row in the
    # topic_err_current then add it and set number of answers to 1.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_answer_after_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_answer_after_upd
        AFTER UPDATE ON answers FOR EACH ROW BEGIN
            DECLARE school INTEGER UNSIGNED DEFAULT NULL;
            DECLARE topic INTEGER UNSIGNED;
            DECLARE qtype INTEGER UNSIGNED;
            DECLARE err SMALLINT DEFAULT -1;

            IF OLD.is_correct != NEW.is_correct THEN
                SELECT school_id INTO school FROM users WHERE
                id=NEW.user_id AND type='student' AND quiz_type=NEW.quiz_type;

                SELECT topic_id, quiz_type INTO topic, qtype FROM questions
                WHERE id=NEW.question_id AND quiz_type=NEW.quiz_type;


                IF NEW.is_correct = 0 THEN
                    SET err=1;
                END IF;

                INSERT INTO topic_err_current VALUES
                (NEW.user_id, qtype, topic, err, 1) ON DUPLICATE KEY UPDATE
                err_count=err_count+VALUES(err_count);

                IF school IS NOT NULL THEN
                    INSERT INTO school_topic_err
                    (school_id, topic_id, quiz_type, err_count, count)
                    VALUES (school, topic, qtype, err, 1) ON DUPLICATE KEY
                    UPDATE err_count=err_count+VALUES(err_count);
                END IF;
            END IF;
        END;
        """))


@add_me
def topic_err_current(mgr):
    # If new entry is added to the topic_err_current table then
    # we also update snapshot of the current state.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_topic_err_current_after_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_topic_err_current_after_add
        AFTER INSERT ON topic_err_current FOR EACH ROW
        INSERT INTO topic_err_snapshot VALUES
        (NEW.user_id, NEW.quiz_type, NEW.topic_id, DATE(UTC_TIMESTAMP()),
         NEW.err_count/NEW.count*100)
        ON DUPLICATE KEY UPDATE err_percent=VALUES(err_percent);
        """))

    # After update we also update snapshot of the current state.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_topic_err_current_after_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_topic_err_current_after_upd
        AFTER UPDATE ON topic_err_current FOR EACH ROW
        INSERT INTO topic_err_snapshot VALUES
        (NEW.user_id, NEW.quiz_type, NEW.topic_id, DATE(UTC_TIMESTAMP()),
         NEW.err_count/NEW.count*100)
        ON DUPLICATE KEY UPDATE err_percent=VALUES(err_percent);
        """))


@add_me
def users(mgr):
    # If guest is added then we update guest access info.
    # If new student is added then create snapshot entry.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_users_after_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_users_after_add
        AFTER INSERT ON users FOR EACH ROW BEGIN
            IF NEW.type = 'guest' THEN
                INSERT IGNORE INTO guest_access VALUES(NEW.id, NEW.quiz_type,
                    0, UTC_TIMESTAMP()+ interval 1 hour);
            ELSE
                INSERT INTO user_progress_snapshot VALUES
                (NEW.id, NEW.quiz_type, DATE(UTC_TIMESTAMP()), NEW.progress_coef)
                ON DUPLICATE KEY UPDATE progress_coef=VALUES(progress_coef);
            END IF;
        END;
        """))

    # If progress_coef is changed for the student then update snapshot entry.
    # If user activity timestamp is changed and if user is guest
    # then we update number of requests.
    # Also last school activity is updated in the school_stat_cache.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_users_after_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_users_after_upd
        AFTER UPDATE ON users FOR EACH ROW BEGIN
            IF NEW.type = 'student' AND NEW.progress_coef != OLD.progress_coef
            THEN
                INSERT INTO user_progress_snapshot VALUES
                (NEW.id, NEW.quiz_type, DATE(UTC_TIMESTAMP()), NEW.progress_coef)
                ON DUPLICATE KEY UPDATE progress_coef=VALUES(progress_coef);
            ELSEIF NEW.type = 'guest' AND NEW.last_visit != OLD.last_visit THEN
                UPDATE guest_access SET num_requests = num_requests + 1
                WHERE id=NEW.id AND quiz_type=NEW.quiz_type;
            END IF;
            INSERT INTO school_stat_cache
            (school_id, quiz_type, last_activity, stat_cache)
            VALUES (NEW.school_id, NEW.quiz_type, UTC_TIMESTAMP(), "")
            ON DUPLICATE KEY UPDATE last_activity=VALUES(last_activity);
        END;
        """))

    # Before delete a user we delete all user's data for all types of quizzes.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_users_before_del;")
    mgr.conn.execute(text("""CREATE TRIGGER on_users_before_del
        BEFORE DELETE ON users FOR EACH ROW BEGIN
            DELETE FROM user_progress_snapshot WHERE user_id=OLD.id;
            DELETE FROM topic_err_current WHERE user_id=OLD.id;
            DELETE FROM topic_err_snapshot WHERE user_id=OLD.id;
            DELETE FROM answers WHERE user_id=OLD.id;
            DELETE FROM quiz_answers WHERE user_id=OLD.id;
            DELETE FROM exams WHERE user_id=OLD.id;
            IF OLD.type = 'guest' THEN
                DELETE FROM guest_access WHERE id=OLD.id;
            END IF;
        END;
        """))


@add_me
def schools(mgr):
    # Stored procedure for update daily snapshot of the school
    # topics statistics. This procedure will be run daily by the update
    # script. See misc/dbupdate.py.
    mgr.conn.execute("DROP PROCEDURE IF EXISTS update_school_snapshot;")
    mgr.conn.execute(text("""CREATE PROCEDURE update_school_snapshot
        (IN school INT UNSIGNED, IN type INT UNSIGNED)
        BEGIN
            DECLARE topic INT UNSIGNED;
            DECLARE qtype INT UNSIGNED;
            DECLARE err FLOAT DEFAULT -1;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT
                topic_id, quiz_type, err_count/count*100 FROM school_topic_err
                WHERE school_id=school AND quiz_type=type;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            OPEN cur;
            START TRANSACTION;
            rloop: LOOP
                FETCH cur INTO topic, qtype, err;
                IF done THEN
                    LEAVE rloop;
                END IF;

                INSERT INTO school_topic_err_snapshot VALUES
                (school, qtype, topic, DATE(UTC_TIMESTAMP()), err)
                ON DUPLICATE KEY UPDATE err_percent=VALUES(err_percent);
            END LOOP;
            COMMIT;
            CLOSE cur;
        END;
        """))


@add_me
def quiz_answers(mgr):
    # Helper function for updating answers.
    mgr.conn.execute("DROP PROCEDURE IF EXISTS upd_answer;")
    mgr.conn.execute(text("""CREATE PROCEDURE upd_answer
        (IN user INTEGER UNSIGNED, IN qtype INTEGER UNSIGNED,
         IN quest INTEGER UNSIGNED, IN correct BOOLEAN)
        BEGIN
            INSERT INTO answers VALUES(user, qtype, quest, correct)
            ON DUPLICATE KEY UPDATE is_correct = VALUES(is_correct);
        END;
        """))

    # After inserting quiz answer we update answers table.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_quiz_answers_after_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_quiz_answers_after_add
        AFTER INSERT ON quiz_answers FOR EACH ROW
        CALL upd_answer(NEW.user_id, NEW.quiz_type, NEW.question_id,
                        NEW.is_correct);
        """))

    # After updating quiz answer we update answers table.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_quiz_answers_after_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_quiz_answers_after_upd
        AFTER UPDATE ON quiz_answers FOR EACH
        ROW CALL upd_answer(NEW.user_id, NEW.quiz_type, NEW.question_id,
                            NEW.is_correct);
        """))


@add_me
def exam_answers(mgr):
    # Before updating exam answer we update answer table.
    # NOTE: since exam ID is unique we don't need to specify
    # question's quiz_type in the WHERE section.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_exam_answers_before_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_exam_answers_before_upd
        BEFORE UPDATE ON exam_answers FOR EACH ROW BEGIN
            DECLARE user INT UNSIGNED;
            SELECT user_id INTO user FROM exams WHERE id=NEW.exam_id;
            CALL upd_answer(user, NEW.quiz_type, NEW.question_id,
                            NEW.is_correct);
        END;
        """))


@add_me
def exams(mgr):
    # Before delete exam we delete exam's answers.
    # NOTE: since exam ID is unique we don't need to specify
    # question's quiz_type.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_exams_before_del;")
    mgr.conn.execute(text("""CREATE TRIGGER on_exams_before_del
        BEFORE DELETE ON exams FOR EACH ROW
        DELETE FROM exam_answers WHERE exam_id=OLD.id;
        """))

    # After update exam info we recalculate err percent
    # of performed exams and save it to the user_progress_snapshot.
    # NOTE: we skip 'in-progress' exams.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_exams_after_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_exams_after_upd
        AFTER UPDATE ON exams FOR EACH ROW BEGIN
            DECLARE coef FLOAT DEFAULT -1;

            SELECT SUM(IF(err_count > 4, 1, 0)) / count(end_time)
            INTO coef FROM exams WHERE user_id=NEW.user_id
            AND quiz_type=NEW.quiz_type;

            UPDATE users SET progress_coef=coef WHERE id=NEW.user_id
            AND quiz_type=NEW.quiz_type;
        END;
        """))


@add_me
def guest_access(mgr):
    # After adding guest info we also add snapshot entry.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_guest_access_after_add;")
    mgr.conn.execute(text("""CREATE TRIGGER on_guest_access_after_add
        AFTER INSERT ON guest_access FOR EACH ROW
        INSERT IGNORE INTO guest_access_snapshot VALUES
        (NEW.id, NEW.quiz_type, DATE(UTC_TIMESTAMP()), 0);
        """))

    # If guest's num_requests is changed then we count snapshot value.
    # NOTE: on_users_after_upd updates num_requests in the guest_access table.
    mgr.conn.execute("DROP TRIGGER IF EXISTS on_guest_access_after_upd;")
    mgr.conn.execute(text("""CREATE TRIGGER on_guest_access_after_upd
        AFTER UPDATE ON guest_access FOR EACH ROW BEGIN
            IF NEW.num_requests != OLD.num_requests THEN
                INSERT INTO guest_access_snapshot VALUES
                (NEW.id, NEW.quiz_type, DATE(UTC_TIMESTAMP()), 1)
                ON DUPLICATE KEY UPDATE num_requests = num_requests + 1;
            END IF;
        END;
        """))
