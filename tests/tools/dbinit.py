#!/usr/bin/env python
''' Script for setup Quiz databse for testing. '''

from __future__ import print_function
import os
import os.path
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'misc'))

import argparse
from sqlalchemy import text
from dbtools import DbManager
import fill
import exampledata


###########################################################
# Configuration
###########################################################

NUM_CHAPTERS = 25
NUM_TOPICS = 10
NUM_QUESTIONS = 200
NUM_SCHOOLS = 200
NUM_STUDENTS = 4
NUM_ANS_QUESTIONS = NUM_QUESTIONS * 0.7
NUM_QUIZ_TYPES = 3


class Db(DbManager):
    def __init__(self):
        self.parseArgs()
        DbManager.__init__(self,
                           self.args.verbose,
                           self.args.config)
        self.put_users = True

    def parseArgs(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Quiz test databse setup tool.')
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output.')
        parser.add_argument('-c', '--config', default=None,
                            help="Configuration file (default: ../test-data/config.ini).")
        parser.add_argument('-s', '--small', action='store_true',
                            help='Create small testing data.')
        parser.add_argument('--qs', action='store_true',
                            help='Generate quiz statistics.')
        parser.add_argument('-p', action='store_true',
                            help="Fill with big data for performance testing.")
        parser.add_argument('-e', action='store_true',
                            help="Fill with example school data.")
        self.args = parser.parse_args()

    # NOTE: Old code, not used.
    # def createUsers(self):
    #     print('Populating: %d schools with %d users per school...'
    #           % (NUM_SCHOOLS, NUM_STUDENTS))

    #     for i in range(1, NUM_SCHOOLS):
    #         vals = []
    #         tmp = 'school%d' % i
    #         vals.append({
    #             'name': tmp,
    #             'login': tmp,
    #             'passwd': self._create_digest(tmp, tmp),
    #             'type': 'school',
    #             'school_id': 0
    #         })
    #         for j in range(1, NUM_STUDENTS):
    #             tmp = 'student%d.%d' % (i, j)
    #             vals.append({
    #                 'name': tmp,
    #                 'login': tmp,
    #                 'passwd': self._create_digest(tmp, tmp),
    #                 'type': 'student',
    #                 'school_id': i
    #             })
    #         self.conn.execute(self.tbl_users.insert(), vals)

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
            """CREATE PROCEDURE aux_chapters(IN type INT)
            BEGIN
                DECLARE i INT DEFAULT 1;
                PREPARE stmt FROM 'INSERT INTO chapters VALUES(?, ?, 1, ?, 0, 0)';
                START TRANSACTION;
                WHILE (i <= {chapters}) DO
                    SET @a = i;
                    SET @b = type;
                    SET @c = CONCAT('chapter ', i, ' type: ', type);
                    EXECUTE stmt USING @a, @b, @c;
                    SET i = i + 1;
                END WHILE;
                COMMIT;
                DEALLOCATE PREPARE stmt;
            END;
            CREATE PROCEDURE aux_topics(IN type INT)
            BEGIN
                DECLARE i INT DEFAULT 1;
                DECLARE j INT DEFAULT 1;
                DECLARE idx INT DEFAULT 1;

                PREPARE stmt FROM 'INSERT INTO topics(id, quiz_type, text, chapter_id) VALUES(?, ?, ?, ?)';
                START TRANSACTION;
                WHILE (i <= {chapters}) DO
                    WHILE (j <= {topics}) DO
                        SET @ix = idx;
                        SET @a = type;
                        SET @b = CONCAT('topic ', i, '.', j, ' type: ', type);
                        SET @c = i;
                        EXECUTE stmt USING @ix, @a, @b, @c;
                        SET j = j + 1;
                        SET idx = idx + 1;
                    END WHILE;
                    SET i = i + 1;
                    SET j = 1;
                END WHILE;
                COMMIT;
                update chapters set priority=2 where id > 10;
                DEALLOCATE PREPARE stmt;
            END;
            CREATE PROCEDURE aux_questions(IN type INT, IN ans INT)
            BEGIN
                DECLARE chap INT DEFAULT 1;
                DECLARE top INT DEFAULT 1;
                DECLARE quest INT DEFAULT 1;
                DECLARE n INT DEFAULT 1;
                DECLARE i INT DEFAULT 1;
                SET n = {chapters} * {topics};

                PREPARE stmt FROM 'INSERT INTO questions(id, quiz_type, text, answer, chapter_id, topic_id) VALUES(?, ?, ?, ?, ?, ?)';
                START TRANSACTION;
                WHILE (chap <= {chapters}) DO
                    WHILE (top <= {topics}) DO
                        WHILE (quest <= {questions}) DO
                            SET @i = i;
                            SET @a = type;
                            SET @b = CONCAT('question ', chap, '.', top, '.', quest, ' type: ', type);
                            SET @c = chap;
                            SET @d = top + (chap - 1) * {topics};
                            SET @answ = ans;
                            EXECUTE stmt USING @i, @a, @b, @answ, @c, @d;
                            SET quest = quest + 1;
                            SET i = i + 1;
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
        self.conn.execute('call aux_chapters(1);')
        self.conn.execute('call aux_chapters(2);')

        print("Populating with test data... topics")
        self.conn.execute('call aux_topics(1);')
        self.conn.execute('call aux_topics(2);')

        print("Populating with test data... questions")
        self.conn.execute('call aux_questions(1, 1);')
        self.conn.execute('call aux_questions(2, 0);')

        if self.args.qs:  # TODO: not worked, fix me
            print("Populating answers...")
            self.conn.execute('call aux_answers();')
        #create_more_users()
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_chapters;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_topics;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_questions;')
        self.conn.execute('DROP PROCEDURE IF EXISTS aux_answers;')

    # TODO: update me to use for new db structure.
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

    def fillData(self):
        if self.args.small:
            self.fillSmallData()
        else:
            self.fillBigData()

    def fillForPerformance(self):
        fill.do_fill(self)

    def fillExample(self):
        exampledata.fill(self)

    def _do_run(self):
        if self.args.p:
            self.fillForPerformance()
        elif self.args.e:
            self.fillExample()
        else:
            DbManager._do_run(self)


Db().run()
