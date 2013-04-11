def do_fill(mgr):
    print("Fill with big data ...")
    create_exams(mgr)
    create_topics_snapshots(mgr)


def create_exams(mgr):
    print("Create exams ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst_exam")
    mgr.conn.execute("""CREATE PROCEDURE tst_exam
        (IN numusers INT, IN numdays INT, IN start CHAR(10))
        BEGIN
            DECLARE user INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            TRUNCATE TABLE exams;
            PREPARE stmt FROM 'INSERT INTO exams(user_id, start_time, end_time, err_count) VALUES(?, ?, ?, ?)';

            SET dt = DATE(start);
            IF dt IS NULL THEN SET dt = DATE(UTC_TIMESTAMP()); END IF;

            START TRANSACTION;
            WHILE (user <= numusers) DO
                SET d = dt;
                WHILE (day <= numdays) DO
                    SET @a = user;
                    SET @b = d;
                    SET @c = DATE_ADD(d, interval 1 hour);
                    SET @d = DATE_ADD(@c, interval 80 MINUTE);
                    SET @e = FLOOR(2 + (RAND() * 6));
                    EXECUTE stmt USING @a, @c, @d, @e;

                    SET @c = DATE_ADD(d, interval 2 hour);
                    SET @d = DATE_ADD(@c, interval 80 MINUTE);
                    SET @e = FLOOR(2 + (RAND() * 6));
                    EXECUTE stmt USING @a, @c, @d, @e;

                    SET @c = DATE_ADD(d, interval 3 hour);
                    SET @d = NULL;
                    SET @e = 0;
                    EXECUTE stmt USING @a, @c, @d, @e;

                    SET day = day + 1;
                    SET d = d - interval 1 day;
                END WHILE;
                SET day = 1;
                SET user = user + 1;
            END WHILE;
            COMMIT;
            DEALLOCATE PREPARE stmt;
        END;""")
    mgr.conn.execute("call tst_exam(40, 60, '')")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst_exam")
    print("Create exams ...done")


def create_topics_snapshots(mgr):
    print("Create topics snapshots ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst_shot")
    mgr.conn.execute("""CREATE PROCEDURE tst_shot
        (IN numusers INT, IN numtopics INT, IN numdays INT, IN start CHAR(10))
        BEGIN
            DECLARE user INT DEFAULT 1;
            DECLARE topic INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;
            DECLARE err FLOAT DEFAULT 0;

            TRUNCATE TABLE topic_err_current;
            TRUNCATE TABLE topic_err_snapshot;
            PREPARE stmt FROM 'INSERT INTO topic_err_snapshot VALUES(?, ?, ?, ?)';
            PREPARE stmt1 FROM 'INSERT INTO topic_err_current VALUES(?, ?, ?, ?)';

            SET dt = DATE(start);

            IF dt IS NULL THEN
                SET dt = DATE(UTC_TIMESTAMP());
            END IF;

            START TRANSACTION;
            WHILE (user <= numusers) DO
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
                SET user = user + 1;
            END WHILE;
            COMMIT;
            DEALLOCATE PREPARE stmt;
            DEALLOCATE PREPARE stmt1;
        END;""")
    mgr.conn.execute("call tst_shot(40, 60, 100, '')")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst_shot")
    print("Create topics snapshots ...done")
