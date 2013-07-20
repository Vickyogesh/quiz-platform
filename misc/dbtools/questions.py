def update_stat(mgr):
    print("Updating questions stat...")
    create_func(mgr)
    mgr.conn.execute('CALL set_chapters_info(1);')
    mgr.conn.execute('CALL set_chapters_info(2);')
    mgr.conn.execute('CALL set_topics_info(1);')
    mgr.conn.execute('CALL set_topics_info(2);')
    mgr.conn.execute('DROP PROCEDURE IF EXISTS set_chapters_info;')
    mgr.conn.execute('DROP PROCEDURE IF EXISTS set_topics_info;')


def create_func(mgr):
    mgr.conn.execute('DROP PROCEDURE IF EXISTS set_chapters_info;')
    mgr.conn.execute("""CREATE PROCEDURE set_chapters_info(IN type INT)
    BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE qtype INTEGER UNSIGNED;
    DECLARE idval INTEGER UNSIGNED;
    DECLARE qmin_id INTEGER UNSIGNED;
    DECLARE qmax_id INTEGER UNSIGNED;

    DECLARE cur CURSOR FOR
    SELECT quiz_type, chapter_id, min(id), max(id) FROM questions
    WHERE quiz_type=type GROUP BY quiz_type, chapter_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;
    OPEN cur;
    ll: LOOP
        FETCH cur INTO qtype, idval, qmin_id, qmax_id;
        IF done THEN
            LEAVE ll;
        END IF;
        UPDATE chapters SET min_id=qmin_id, max_id=qmax_id
        WHERE id=idval AND quiz_type=qtype;
    END LOOP;
    CLOSE cur;
    COMMIT;
    END;
    """)

    mgr.conn.execute('DROP PROCEDURE IF EXISTS set_topics_info;')
    mgr.conn.execute("""CREATE PROCEDURE set_topics_info(IN type INT)
    BEGIN
    DECLARE done INT DEFAULT FALSE;
    DECLARE qtype INTEGER UNSIGNED;
    DECLARE idval INTEGER UNSIGNED;
    DECLARE qmin_id INTEGER UNSIGNED;
    DECLARE qmax_id INTEGER UNSIGNED;

    DECLARE cur CURSOR FOR
    SELECT quiz_type, topic_id, min(id), max(id) FROM questions
    WHERE quiz_type=type GROUP BY quiz_type, topic_id;

    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    START TRANSACTION;
    OPEN cur;
    ll: LOOP
        FETCH cur INTO qtype, idval, qmin_id, qmax_id;
        IF done THEN
            LEAVE ll;
        END IF;
        UPDATE topics SET min_id=qmin_id, max_id=qmax_id
        WHERE id=idval AND quiz_type=qtype;
    END LOOP;
    CLOSE cur;
    COMMIT;
    END;
    """)
