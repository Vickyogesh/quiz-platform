def do_fill(mgr):
    print("Fill with big data ...")
    create_users(mgr)
    create_guestvisits(mgr)
    create_exams(mgr)
    create_user_progress(mgr)
    create_school_topic_err_snapshot(mgr)
    create_topics_snapshots(mgr)


def create_users(mgr):
    print("Create users ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.conn.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE schools INT DEFAULT 40;
            DECLARE school INT DEFAULT 1;
            DECLARE users INT DEFAULT 140;
            DECLARE user INT DEFAULT 1;

            TRUNCATE TABLE schools;
            TRUNCATE TABLE users;
            TRUNCATE TABLE user_progress_snapshot;
            TRUNCATE TABLE guest_access;
            TRUNCATE TABLE guest_access_snapshot;

            START TRANSACTION;
            WHILE (school <= schools) DO
                SET @a = CONCAT('school_', school);

                INSERT INTO schools VALUES(0, @a, @a, MD5(CONCAT(@a, ':', @a)));

                WHILE (user <= users) DO
                    SET @a = CONCAT('user_', school, '_', user);
                    INSERT INTO users VALUES
                    (0, @a, @a, @a, MD5(CONCAT(@a, ':', @a)), 'student', school, UTC_TIMESTAMP(), -1);

                    SET user = user + 1;
                END WHILE;

                SET school = school + 1;
                SET user = 1;
            END WHILE;
            COMMIT;
        END;""")
    mgr.conn.execute("call tst()")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create users ...done")


def create_guestvisits(mgr):
    print("Create guest visits ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.conn.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE i INT DEFAULT 1;
            DECLARE numdays INT DEFAULT 35;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT id FROM guest_access;
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
                    VALUES(i, d, FLOOR(20 + (RAND() * 80)));

                    SET day = day + 1;
                    SET d = d - interval 1 day;
                END WHILE;
                SET day = 1;
            END LOOP;
            COMMIT;

            CLOSE cur;
        END;""")
    mgr.conn.execute("call tst()")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create uest visits ...done")


def create_exams(mgr):
    print("Create exams ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.conn.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE numdays INT DEFAULT 35;
            DECLARE user INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT id FROM users WHERE type='student';
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            TRUNCATE TABLE exams;
            PREPARE stmt FROM 'INSERT INTO exams(user_id, start_time, end_time, err_count) VALUES(?, ?, ?, ?)';

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
            END LOOP;
            COMMIT;
            DEALLOCATE PREPARE stmt;
            CLOSE cur;
        END;""")
    mgr.conn.execute("call tst()")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create exams ...done")


def create_user_progress(mgr):
    print("Create user progress ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.conn.execute("""CREATE PROCEDURE tst()
        BEGIN
            DECLARE numdays INT DEFAULT 35;
            DECLARE user INT DEFAULT 1;
            DECLARE day INT DEFAULT 1;
            DECLARE dt DATE DEFAULT NULL;
            DECLARE d DATE DEFAULT NULL;

            DECLARE done INT DEFAULT FALSE;
            DECLARE cur CURSOR FOR SELECT id FROM users WHERE type='student';
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            TRUNCATE TABLE user_progress_snapshot;
            PREPARE stmt FROM 'INSERT INTO user_progress_snapshot VALUES(?, ?, ?)';

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
        END;""")
    mgr.conn.execute("call tst()")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create user progress ...done")


def create_school_topic_err_snapshot(mgr):
    print("Create schools topic_err snapshots ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.conn.execute("""CREATE PROCEDURE tst()
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
            DECLARE cur CURSOR FOR SELECT id FROM schools;
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            PREPARE stmt FROM 'INSERT INTO school_topic_err_snapshot VALUES(?, ?, ?, ?)';

            SET dt = DATE(UTC_TIMESTAMP());
            OPEN cur;

            TRUNCATE TABLE school_topic_err_snapshot;

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
        END;""")
    mgr.conn.execute("call tst()")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create uest visits ...done")


def create_topics_snapshots(mgr):
    print("Create topics snapshots ...")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    mgr.conn.execute("""CREATE PROCEDURE tst()
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
            DECLARE cur CURSOR FOR SELECT id FROM users WHERE type='student';
            DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

            TRUNCATE TABLE topic_err_current;
            TRUNCATE TABLE topic_err_snapshot;
            PREPARE stmt FROM 'INSERT INTO topic_err_snapshot VALUES(?, ?, ?, ?)';
            PREPARE stmt1 FROM 'INSERT INTO topic_err_current VALUES(?, ?, ?, ?)';

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
        END;""")
    mgr.conn.execute("call tst()")
    mgr.conn.execute("DROP PROCEDURE IF EXISTS tst")
    print("Create topics snapshots ...done")
