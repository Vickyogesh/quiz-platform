def update_stat(mgr):
    print("Updating questions stat...")
    mgr.conn.execute('DROP PROCEDURE IF EXISTS update_data_stat;')
    mgr.conn.execute("""CREATE PROCEDURE update_data_stat()
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

    mgr.conn.execute('call update_data_stat();')
    mgr.conn.execute('DROP PROCEDURE IF EXISTS update_data_stat;')
