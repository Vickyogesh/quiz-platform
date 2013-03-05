#!/usr/bin/env python
''' Script for setup Quiz databse for testing. '''

from __future__ import print_function
import os
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'misc'))

import argparse
from sqlalchemy import text
from dbtools import DbTool

###########################################################
# Configuration
###########################################################

NUM_CHAPTERS = 25
NUM_TOPICS = 10
NUM_QUESTIONS = 200
NUM_SCHOOLS = 200
NUM_STUDENTS = 4
NUM_ANS_QUESTIONS = NUM_QUESTIONS * 0.7


# def errtable():
    # ctx.engine.execute(text('DROP TABLE IF EXISTS error_stat;'))
    # ctx.engine.execute(text('DROP TABLE IF EXISTS topic_stat;'))

    # sql = """ CREATE TABLE topic_stat(
    #         user_id INTEGER UNSIGNED NOT NULL,
    #         topic_id INTEGER UNSIGNED NOT NULL,
    #         error_percent SMALLINT NOT NULL DEFAULT 0
    #     )
    #     ALTER TABLE topic_stat ADD UNIQUE ix_err(user_id, topic_id);

    #     CREATE TABLE error_stat(
    #         user_id INTEGER UNSIGNED NOT NULL,
    #         question_id INTEGER UNSIGNED NOT NULL
    #     );
    #     ALTER TABLE error_stat ADD UNIQUE ix_err(question_id, user_id);

    #     DROP TRIGGER IF EXISTS tg_error_update;
    #     CREATE TRIGGER tg_error_update AFTER INSERT ON quiz_stat
    #     FOR EACH ROW DELETE FROM error_stat
    #         WHERE user_id=NEW.user_id AND question_id=NEW.question_id;
    # """
    # ctx.engine.execute(sql)

class Db(DbTool):
    def __init__(self):
        self.parseArgs()
        DbTool.__init__(self,
                        self.args.verbose,
                        self.args.new,
                        self.args.config)
        self._users = DbTool.TEST_USERS

    def parseArgs(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Quiz test databse setup tool.')
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output.')
        parser.add_argument('-n', '--new', action='store_true',
                            help='Create quiz database.')
        parser.add_argument('-s', '--small', action='store_true',
                            help='Create small testing data.')
        parser.add_argument('--qs', action='store_true',
                            help='Generate quiz statistics.')
        parser.add_argument('-c', '--config', default=None,
                            help="Configuration file (default: ../test-data/config.ini).")
        self.args = parser.parse_args()

    def createUsers(self):
        print('Populating: %d schools with %d users per school...'
              % (NUM_SCHOOLS, NUM_STUDENTS))

        for i in range(1, NUM_SCHOOLS):
            vals = []
            tmp = 'school%d' % i
            vals.append({
                'name': tmp,
                'login': tmp,
                'passwd': self._create_digest(tmp, tmp),
                'type': 'school',
                'school_id': None
            })
            for j in range(1, NUM_STUDENTS):
                tmp = 'student%d.%d' % (i, j)
                vals.append({
                    'name': tmp,
                    'login': tmp,
                    'passwd': self._create_digest(tmp, tmp),
                    'type': 'student',
                    'school_id': i
                })
            self.conn.execute(self.tbl_users.insert(), vals)

    def fillBigData(self):
        print("Preparing to populate with test data...")
        self.conn.execute('TRUNCATE TABLE chapters;')
        self.conn.execute('TRUNCATE TABLE topics;')
        self.conn.execute('TRUNCATE TABLE questions;')
        self.conn.execute('TRUNCATE TABLE quiz_stat;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_chapters;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_topics;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_questions;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_qstat;')

        self.conn.execute(text(
            """CREATE PROCEDURE aux_chapters()
            BEGIN
                DECLARE i INT DEFAULT 1;
                PREPARE stmt FROM 'INSERT INTO chapters VALUES(?, 1, ?, 0, 0)';
                START TRANSACTION;
                WHILE (i <= {chapters}) DO
                    SET @a = i;
                    SET @b = CONCAT('chapter ', i);
                    EXECUTE stmt USING @a, @b;
                    SET i = i + 1;
                END WHILE;
                COMMIT;
                DEALLOCATE PREPARE stmt;
            END;
            CREATE PROCEDURE aux_topics()
            BEGIN
                DECLARE i INT DEFAULT 1;
                DECLARE j INT DEFAULT 1;

                PREPARE stmt FROM 'INSERT INTO topics(text, chapter_id) VALUES(?, ?)';
                START TRANSACTION;
                WHILE (i <= {chapters}) DO
                    WHILE (j <= {topics}) DO
                        SET @a = CONCAT('topic ', i, '.', j);
                        SET @b = i;
                        EXECUTE stmt USING @a, @b;
                        SET j = j + 1;
                    END WHILE;
                    SET i = i + 1;
                    SET j = 1;
                END WHILE;
                COMMIT;
                update chapters set priority=2 where id > 10;
                DEALLOCATE PREPARE stmt;
            END;
            CREATE PROCEDURE aux_questions()
            BEGIN
                DECLARE chap INT DEFAULT 1;
                DECLARE top INT DEFAULT 1;
                DECLARE quest INT DEFAULT 1;
                DECLARE n INT DEFAULT 1;
                SET n = {chapters} * {topics};

                PREPARE stmt FROM 'INSERT INTO questions(text, answer, chapter_id, topic_id) VALUES(?, 1, ?, ?)';
                START TRANSACTION;
                WHILE (chap <= {chapters}) DO
                    WHILE (top <= {topics}) DO
                        WHILE (quest <= {questions}) DO
                            SET @a = CONCAT('question ', chap, '.', top, '.', quest);
                            SET @b = chap;
                            SET @c = top + (chap - 1) * {topics};
                            EXECUTE stmt USING @a, @b, @c;
                            SET quest = quest + 1;
                        END WHILE;
                        SET top = top + 1;
                        SET quest = 1;
                    END WHILE;
                    SET chap = chap + 1;
                    SET top = 1;
                END WHILE;
                COMMIT;
                DEALLOCATE PREPARE stmt;
            END;
            CREATE PROCEDURE aux_qstat()
            BEGIN
                DECLARE user INT DEFAULT 1;
                DECLARE topic INT DEFAULT 1;
                DECLARE quest INT DEFAULT 1;
                DECLARE nun_topics INT DEFAULT 1;
                DECLARE qid INT DEFAULT 1;
                DECLARE correct INT DEFAULT 1;

                SET nun_topics = {chapters} * {topics};

                PREPARE stmt FROM 'INSERT INTO quiz_stat VALUES(?, ?, ?)';
                START TRANSACTION;
                WHILE (user <= {num_users}) DO
                    WHILE (topic <= nun_topics) DO
                        SET correct = 1;
                        WHILE (quest <= {num_ans}) DO
                            SET @a = user;
                            SET @b = correct < 2;
                            SET @c = quest + (topic - 1) * {questions};
                            EXECUTE stmt USING @a, @b, @c;
                            SET quest = quest + 1;
                            SET correct = correct + 1;
                        END WHILE;
                        SET topic = topic + 1;
                        SET quest = 1;
                    END WHILE;
                    SET user = user + 1;
                    SET topic = 1;
                    SET quest = 1;
                END WHILE;
                COMMIT;
                DEALLOCATE PREPARE stmt;
            END;
            """.format(chapters=NUM_CHAPTERS,
                       topics=NUM_TOPICS,
                       questions=NUM_QUESTIONS,
                       num_users=20,
                       num_ans=NUM_ANS_QUESTIONS)))

        print("Populating with test data... chapters")
        self.conn.execute('call aux_chapters();')

        print("Populating with test data... topics")
        self.conn.execute('call aux_topics();')

        print("Populating with test data... questions")
        self.conn.execute('call aux_questions();')

        if self.args.qs:
            print("Populating quiz stat...")
            self.conn.execute('call aux_qstat();')
        #create_more_users()

    def fillSmallData(self):
        print("Preparing to populate with SMALL test data...")
        self.conn.execute('TRUNCATE TABLE chapters;')
        self.conn.execute('TRUNCATE TABLE topics;')
        self.conn.execute('TRUNCATE TABLE questions;')
        self.conn.execute('TRUNCATE TABLE quiz_stat;')

        chapters = [1, 2, 3]
        topics = range(1, 3)
        questions = range(1, 101)

        print("Creating chapters...")
        sql = text("INSERT INTO chapters VALUES(0, 1, :txt)")
        for i in chapters:
            self.conn.execute(sql, txt='chapter %d' % i)

        print("Creating topics...")
        sql = text("INSERT INTO topics VALUES(0, :txt, :txt, :txt, :ch)")
        for ch in chapters:
            for t in topics:
                self.conn.execute(sql, txt='topic %d.%d' % (ch, t), ch=ch)

        print("Creating questions...")
        sql = text("""INSERT INTO questions VALUES
                   (0, :txt, :txt, :txt, :ans, '', '', :ch, :topic)""")
        top = 1
        for ch in chapters:
            for t in topics:
                for q in questions:
                    txt = '%d.%d.%d Question' % (ch, t, q)
                    self.conn.execute(sql, txt=txt, ans=1, ch=ch, topic=top)
                top += 1

    def fillData(self):
        if self.args.small:
            self.fillSmallData()
        else:
            self.fillBigData()

Db().run()
