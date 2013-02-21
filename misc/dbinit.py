#!/usr/bin/env python
''' Script for setup Quiz databse. '''

from __future__ import print_function
import os
import os.path
import sys

# to use settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))

import argparse
import hashlib
import csv
from sqlalchemy import create_engine, MetaData, text
from quiz.settings import Settings


###########################################################
# Configuration
###########################################################

# Input files
CHAPTERS_FILE = "dbdata/chapters.csv"
TOPICS_FILE = "dbdata/topics.csv"
QUESTIONS_FILE = "dbdata/questions.csv"

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

# Default users
REAL_USERS = [
    {
        'name': 'Admin',
        'login': 'root',
        'passwd': 'ari09Xsw_',
        'type':'admin'
    }]

# Test users
TEST_USERS = [
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
    description='Quiz databse setup tool.', epilog='''
    Examples.
    Setup database on a clean system with real users and populate with data:
            dbsetup.py -n -c config.ini

    Recreate tables and fill them with data:
            dbsetup.py -c config.ini

    Recreate tables and fill them with data and test users:
            dbsetup.py -t -c config.ini

    NOTE: To recreate tables, fill them with data and
    test users using default config just run: dbsetup.py
    ''')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Verbose output.')
parser.add_argument('-c', '--config', default='',
                    help="Configuration file (default: ../test-data/config.ini).")
parser.add_argument('-n', '--new', action='store_true',
                    help='Create quiz database.')
parser.add_argument('-t', '--test-users', action='store_true',
                    help='Initialize with test users instead of real.')
parser.add_argument('-d', '--delimiter', default='$',
                    help="CSV delimiter (default: '%(default)s').")
args = parser.parse_args()


###########################################################
# Settings setup
###########################################################

if len(args.config) == 0:
    path = os.path.join(os.path.dirname(__file__),
                        '..',
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


def create_users(test_users):
    if test_users:
        print('Creating test users...')
        users = TEST_USERS
    else:
        print('Creating users...')
        users = REAL_USERS

    vals = []
    for user in users:
        user['passwd'] = _create_digest(user['login'], user['passwd'])
        vals.append(user)
    ctx.conn.execute(ctx.tbl_users.insert(), vals)


def fill_chapters():
    print('Populating chapters...')
    path = os.path.join(os.path.dirname(__file__), CHAPTERS_FILE)
    with open(path, "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter=args.delimiter)
        lines = []
        is_first = True
        for row in reader:
            if is_first:
                is_first = False
                continue
            lines.append({'priority': row[2], 'text': row[1]})
        ctx.conn.execute(ctx.tbl_chapters.insert(), lines)


def fill_topics():
    print('Populating topics...')
    path = os.path.join(os.path.dirname(__file__), TOPICS_FILE)
    with open(path, "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter=args.delimiter)
        lines = []
        is_first = True
        for row in reader:
            if is_first:
                is_first = False
                continue
            lines.append({
                'text': row[1],
                'text_fr': row[4],
                'text_de': row[5],
                'chapter_id': row[2]
            })
        ctx.conn.execute(ctx.tbl_topics.insert(), lines)


def fill_questions():
    print('Populating questions...')
    path = os.path.join(os.path.dirname(__file__), QUESTIONS_FILE)
    with open(path, "rb") as csvfile:
        reader = csv.reader(csvfile, delimiter=args.delimiter)
        lines = []
        is_first = True
        for row in reader:
            if is_first:
                is_first = False
                continue
            lines.append({
                'text': row[7],
                'text_fr': row[11],
                'text_de': row[12],
                'answer': row[8] == 'V',
                'image': row[9],
                'image_part': row[10],
                'chapter_id': row[1],
                'topic_id': row[4]
            })
        ctx.conn.execute(ctx.tbl_questions.insert(), lines)


###########################################################
# Action!
###########################################################

if args.new:
    create_db()

setup()

t = ctx.conn.begin()
try:
    drop_tables()
    create_tables()
    fill_apps()
    create_users(args.test_users)
    fill_chapters()
    fill_topics()
    fill_questions()
except Exception as e:
    print(e)
    print('Rollback changes...')
    t.rollback()
except:
    print('Rollback changes...')
    t.rollback()
else:
    t.commit()
