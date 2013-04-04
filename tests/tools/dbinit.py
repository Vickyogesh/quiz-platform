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


class Db(DbTool):
    def __init__(self):
        self.parseArgs()
        DbTool.__init__(self,
                        self.args.verbose,
                        self.args.new,
                        self.args.config)
        self.put_users = True

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
                'school_id': 0
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
        self.conn.execute('TRUNCATE TABLE answers;')
        self.conn.execute('TRUNCATE TABLE quiz_answers;')
        self.conn.execute('TRUNCATE TABLE exam_answers;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_chapters;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_topics;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_questions;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_answers;')

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
            CREATE PROCEDURE aux_answers()
            BEGIN
                DECLARE user INT DEFAULT 1;
                DECLARE topic INT DEFAULT 1;
                DECLARE quest INT DEFAULT 1;
                DECLARE nun_topics INT DEFAULT 1;
                DECLARE qid INT DEFAULT 1;
                DECLARE correct INT DEFAULT 1;

                SET nun_topics = {chapters} * {topics};

                PREPARE stmt FROM 'INSERT INTO answers VALUES(?, ?, ?)';
                START TRANSACTION;
                WHILE (user <= {num_users}) DO
                    WHILE (topic <= nun_topics) DO
                        SET correct = 1;
                        WHILE (quest <= {num_ans}) DO
                            SET @a = user;
                            SET @b = quest + (topic - 1) * {questions};
                            SET @c = correct < 2;
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
            print("Populating answers...")
            self.conn.execute('call aux_answers();')
        #create_more_users()
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_chapters;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_topics;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_questions;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_answers;')

    def fillSmallData(self):
        print("Preparing to populate with SMALL test data...")
        self.conn.execute('TRUNCATE TABLE chapters;')
        self.conn.execute('TRUNCATE TABLE topics;')
        self.conn.execute('TRUNCATE TABLE questions;')
        self.conn.execute('TRUNCATE TABLE answers;')

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

    # see tests/core/test_admin.py
    def createTestFunc(self):
        sql = """CREATE PROCEDURE aux_create_test_users() BEGIN
            TRUNCATE TABLE schools;
            TRUNCATE TABLE users;
            """

        lst = []
        for x in DbTool.TEST_SCHOOLS:
            lst.append("""INSERT INTO schools VALUES
            (0, '{name}', '{login}',
            '{passwd}');""".format(**x))
        sql += '\n'.join(lst)

        lst = []
        for x in DbTool.TEST_USERS:
            lst.append("""INSERT INTO users(name, surname, login, passwd,
            type, school_id) VALUES ('{name}', '{surname}', '{login}',
            '{passwd}', '{type}', {school_id});""".format(**x))

        sql += '\n'.join(lst) + ' END;'
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_create_test_users;')
        self.conn.execute(sql)

    def fillData(self):
        if self.args.small:
            self.fillSmallData()
        else:
            self.fillBigData()
        self.createTestFunc()

Db().run()
