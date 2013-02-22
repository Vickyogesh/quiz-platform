#!/usr/bin/env python
''' Script for setup Quiz databse for testing. '''

from __future__ import print_function
import os
import os.path
import sys

# to use settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

import argparse
import hashlib
from sqlalchemy import create_engine, MetaData, text
from quiz.settings import Settings


###########################################################
# Configuration
###########################################################

NUM_CHAPTERS = 20
NUM_TOPICS = 40
NUM_QUESTIONS = 200

# application keys
APPLICATIONS = [
    {
        'appkey': 'd1053fc29b0e07c7173890db4be19515bc04ae48',
        'description': 'mobileapp'
    },
    {
        'appkey': '32bfe1c505d4a2a042bafd53993f10ece3ccddca',
        'description': 'webapp'
    },
    {
        'appkey': 'b929d0c46cf5609e0104e50d301b0b8b482e9bfc',
        'description': 'desktopapp'
    }]

# Test users
USERS = [
    {
        'name': 'Test User',
        'login': 'testuser',
        'passwd': 'testpasswd',
        'type':'student'
    },
    {
        'name': 'Admin',
        'login': 'root',
        'passwd': 'adminpwd',
        'type':'admin'
    },
    {
        'name': 'Chuck Norris',
        'login': 'chuck@norris.com',
        'passwd': 'boo',
        'type':'school'
    }]


###########################################################
# Script arguments
###########################################################

parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Quiz test databse setup tool.')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Verbose output.')
parser.add_argument('-n', '--new', action='store_true',
                    help='Create quiz database.')
parser.add_argument('-s', '--small', action='store_true',
                    help='Create small testing data.')
parser.add_argument('-c', '--config', default='',
                    help="Configuration file (default: ../test-data/config.ini).")
args = parser.parse_args()


###########################################################
# Settings setup
###########################################################

if len(args.config) == 0:
    path = os.path.join(os.path.dirname(__file__),
                        '..', '..',
                        'test-data',
                        'config.ini')
    paths = os.path.split(os.path.abspath(path))
else:
    paths = os.path.split(args.config)

Settings.CONFIG_FILE = paths[1]
settings = Settings([paths[0]])


class Context(object):
    pass
ctx = Context()


###########################################################
# Functions
###########################################################

def setup():
    print('Setup...')
    global ctx
    ctx.engine = create_engine(settings.dbinfo['database'], echo=args.verbose)
    ctx.conn = ctx.engine.connect()


def drop_tables():
    print('Removing tables...')
    ctx.engine.execute(text('DROP TABLE IF EXISTS applications;'))
    ctx.engine.execute(text('DROP TABLE IF EXISTS users;'))
    ctx.engine.execute(text('DROP TABLE IF EXISTS chapters;'))
    ctx.engine.execute(text('DROP TABLE IF EXISTS topics;'))
    ctx.engine.execute(text('DROP TABLE IF EXISTS questions;'))
    ctx.engine.execute(text('DROP TABLE IF EXISTS quiz_stat;'))


def create_db():
    print('Creating db...')
    engine = create_engine(settings.dbinfo['uri'], echo=args.verbose)
    engine.execute("CREATE DATABASE IF NOT EXISTS quiz")


def create_tables():
    print('Creating tables...')
    ctx.conn.execute(text(
        """
        CREATE TABLE applications(
            id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
            appkey VARCHAR(50) NOT NULL,
            description VARCHAR(100),
            CONSTRAINT PRIMARY KEY (id),
            CONSTRAINT UNIQUE (appkey)
        );

        CREATE TABLE users(
            id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            login VARCHAR(100) NOT NULL,
            passwd VARCHAR(100) NOT NULL,
            type ENUM('admin', 'school', 'student', 'guest') NOT NULL,
            school_id INTEGER UNSIGNED,
            CONSTRAINT PRIMARY KEY (id),
            CONSTRAINT UNIQUE (login)
        );

        CREATE TABLE chapters(
            id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT,
            priority TINYINT UNSIGNED NOT NULL,
            text VARCHAR(100) NOT NULL,
            CONSTRAINT PRIMARY KEY (id)
        );

        CREATE TABLE topics(
            id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
            text VARCHAR(200) NOT NULL,
            text_fr VARCHAR(200),
            text_de VARCHAR(200),
            chapter_id SMALLINT UNSIGNED,
            CONSTRAINT PRIMARY KEY (id)
        );
        ALTER TABLE topics ADD INDEX ix_chid(chapter_id);

        CREATE TABLE questions(
            id INTEGER UNSIGNED NOT NULL AUTO_INCREMENT,
            text VARCHAR(256) NOT NULL,
            text_fr VARCHAR(256),
            text_de VARCHAR(256),
            answer BOOLEAN NOT NULL,
            image VARCHAR(10),
            image_part VARCHAR(10),
            chapter_id SMALLINT UNSIGNED NOT NULL,
            topic_id INTEGER UNSIGNED NOT NULL,
            CONSTRAINT PRIMARY KEY (id)
        );
        ALTER TABLE questions ADD INDEX ix_tp(topic_id);

        CREATE TABLE quiz_stat(
            user_id INTEGER UNSIGNED NOT NULL,
            question_id INTEGER UNSIGNED NOT NULL
        );
        ALTER TABLE quiz_stat ADD UNIQUE ix_quiz(question_id, user_id);
        """))

    ctx.meta = MetaData()
    ctx.meta.reflect(bind=ctx.engine)
    ctx.tbl_apps = ctx.meta.tables['applications']
    ctx.tbl_users = ctx.meta.tables['users']
    ctx.tbl_chapters = ctx.meta.tables['chapters']
    ctx.tbl_topics = ctx.meta.tables['topics']
    ctx.tbl_questions = ctx.meta.tables['questions']
    ctx.tbl_quizstat = ctx.meta.tables['quiz_stat']


def fill_apps():
    print('Populating applications...')
    ctx.conn.execute(ctx.tbl_apps.insert(), APPLICATIONS)


def _create_digest(username, passwd):
    m = hashlib.md5()
    m.update('%s:%s' % (username, passwd))
    return m.hexdigest()


def create_users():
    print("Populating users with test entries...")
    vals = []
    for user in USERS:
        user['passwd'] = _create_digest(user['login'], user['passwd'])
        vals.append(user)
    ctx.conn.execute(ctx.tbl_users.insert(), vals)


def create_more_users():
    print("Populating users with more entries...")
    vals = []
    for i in range(50):
        tmp = 'testuser%d' % i
        vals.append({
            'name': tmp,
            'login': tmp,
            'passwd': _create_digest(tmp, tmp),
            'type': 'student'
        })
    ctx.conn.execute(ctx.tbl_users.insert(), vals)


def populate_big():
    print("Preparing to populate with test data...")
    ctx.conn.execute(text('TRUNCATE TABLE chapter;'))
    ctx.conn.execute(text('TRUNCATE TABLE topic;'))
    ctx.conn.execute(text('TRUNCATE TABLE questions;'))
    ctx.conn.execute(text('TRUNCATE TABLE quiz_stat;'))
    ctx.conn.execute(text('DROP PROCEDURE IF EXISTS aux_chapters;'))
    ctx.conn.execute(text('DROP PROCEDURE IF EXISTS aux_topics;'))
    ctx.conn.execute(text('DROP PROCEDURE IF EXISTS aux_questions;'))

    ctx.conn.execute(text(
        '''CREATE PROCEDURE aux_chapters()
        BEGIN
            DECLARE i INT DEFAULT 1;
            WHILE (i <= {chapters}) DO
                INSERT INTO chapter VALUES(i, 1, CONCAT('chapter ', i));
                SET i = i + 1;
            END WHILE;
        END;
        CREATE PROCEDURE aux_topics()
        BEGIN
            DECLARE i INT DEFAULT 1;
            DECLARE j INT DEFAULT 1;
            WHILE (i <= {chapters}) DO
                WHILE (j <= {topics}) DO
                    INSERT INTO topic(text, chapter_id) VALUES(CONCAT('topic ', i, '.', j), i);
                    SET j = j + 1;
                END WHILE;
                SET i = i + 1;
                SET j = 1;
            END WHILE;
        END;
        CREATE PROCEDURE aux_questions()
        BEGIN
            DECLARE i INT DEFAULT 1;
            DECLARE j INT DEFAULT 1;
            DECLARE k INT DEFAULT 1;
            DECLARE n INT DEFAULT 1;
            SET n = {chapters} * {topics};
            WHILE (i <= {chapters}) DO
                WHILE (j <= n) DO
                    WHILE (k <= {questions}) DO
                        INSERT INTO questions(text, answer, chapter_id, topic_id) VALUES(CONCAT('question ', j, '.', k), 1, i, j);
                        SET k = k + 1;
                    END WHILE;
                    SET j = j + 1;
                    SET k = 1;
                END WHILE;
                SET i = i + 1;
            END WHILE;
        END;
        '''.format(chapters=NUM_CHAPTERS,
                   topics=NUM_TOPICS,
                   questions=NUM_QUESTIONS)))

    print("Populating with test data...")
    ctx.conn.execute(text('call aux_chapters();'))
    ctx.conn.execute(text('call aux_topics();'))
    ctx.conn.execute(text('call aux_questions();'))
    ctx.conn.execute(text('DROP PROCEDURE IF EXISTS aux_chapters;'))
    ctx.conn.execute(text('DROP PROCEDURE IF EXISTS aux_topics;'))
    ctx.conn.execute(text('DROP PROCEDURE IF EXISTS aux_questions;'))
    create_more_users()
    populate_quiz_stat()


def populate_quiz_stat():
    import random
    print("Populating quiz stat...")
    sql = text("INSERT INTO quiz_stat VALUES(:id, :quest)")
    for u in range(1, 5):
        print('for user %d' % u)
        for topic in range(1, random.randint(15, 20)):
            for q in range(1, random.randint(40, 100)):
                qid = q + (topic - 1) * NUM_QUESTIONS
                ctx.conn.execute(sql, id=u, quest=qid)


def populate_small():
    print("Preparing to populate with SMALL test data...")
    ctx.conn.execute(text('TRUNCATE TABLE chapter;'))
    ctx.conn.execute(text('TRUNCATE TABLE topic;'))
    ctx.conn.execute(text('TRUNCATE TABLE questions;'))
    ctx.conn.execute(text('TRUNCATE TABLE quiz_stat;'))

    chapters = [1, 2, 3]
    topics = range(1, 3)
    questions = range(1, 101)

    print("Creating chapters...")
    sql = text("INSERT INTO chapters VALUES(0, 1, :txt)")
    for i in chapters:
        ctx.conn.execute(sql, txt='chapter %d' % i)

    print("Creating topics...")
    sql = text("INSERT INTO topics VALUES(0, :txt, :txt, :txt, :ch)")
    for ch in chapters:
        for t in topics:
            ctx.conn.execute(sql, txt='topic %d.%d' % (ch, t), ch=ch)

    print("Creating questions...")
    sql = text("""INSERT INTO questions VALUES
               (0, :txt, :txt, :txt, :ans, '', '', :ch, :topic)""")
    top = 1
    for ch in chapters:
        for t in topics:
            for q in questions:
                txt = '%d.%d.%d Question' % (ch, t, q)
                ctx.conn.execute(sql, txt=txt, ans=1, ch=ch, topic=top)
            top += 1


def actions():
    drop_tables()
    create_tables()
    fill_apps()
    create_users()

    if args.small:
        populate_small()
    else:
        populate_big()


###########################################################
# Action!
###########################################################

if args.new:
    create_db()

setup()

t = ctx.conn.begin()
try:
    actions()
except Exception as e:
    print(e)
    print('Rollback changes...')
    t.rollback()
except:
    print('Rollback changes...')
    t.rollback()
else:
    t.commit()
