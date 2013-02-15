#!/usr/bin/env python
""" Script for setup Quiz databse. """

from __future__ import print_function
import os
import os.path
import sys

# to use settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))

import argparse
import csv
from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import String, Enum, ForeignKey, Boolean
from sqlalchemy.dialects.mysql import SMALLINT as SmallInteger
from sqlalchemy.dialects.mysql import TINYINT as TinylInteger
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
    Setup database on a clean system without users and populate with data:
            dbsetup.py -nif

    Recreate tables and populate with users:
            dbsetup.py -i -u real
    ''')
parser.add_argument('-v', '--verbose', action='store_true',
                    help='Verbose output')
parser.add_argument('-c', '--config', default='',
                    help="Configuration file (default: ../data/config.ini)")
parser.add_argument('-n', '--new', action='store_true',
                    help='Create quiz database')
parser.add_argument('-i', '--init', action='store_true',
                    help='Initialize DB (create tables)')
parser.add_argument('-u', '--users', choices=['test', 'real'],
                    help='Initialize with users (default: %(default)s)')
parser.add_argument('-f', '--fill', action='store_true',
                    help="Fill database")
parser.add_argument('-d', '--delimiter', default='$',
                    help="CSV delimiter (default: '%(default)s')")
args = parser.parse_args()


# setup settings
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


def create_db():
    print('Creating db...')
    engine = create_engine(settings.dbinfo['uri'], echo=args.verbose)
    engine.execute("CREATE DATABASE IF NOT EXISTS quiz")


def prepare_db():
    global ctx
    ctx.engine = create_engine(settings.dbinfo['database'], echo=args.verbose)
    ctx.meta = MetaData()
    ctx.conn = ctx.engine.connect()

    ctx.tbl_apps = Table('applications', ctx.meta,
        Column('id', SmallInteger(unsigned=True), autoincrement=True,
               primary_key=True),
        Column('appkey', String(50), nullable=False, unique=True),
        Column('description', String(100))
    )

    ctx.tbl_users = Table('users', ctx.meta,
        Column('id', SmallInteger(unsigned=True), autoincrement=True,
               primary_key=True),
        Column('name', String(100), nullable=False),
        Column('login', String(100), nullable=False, unique=True),
        Column('passwd', String(100), nullable=False),
        Column('type', Enum('admin', 'school', 'student', 'guest'),
               nullable=False),
        Column('school_id', SmallInteger(unsigned=True))
    )

    ctx.tbl_chapter = Table('chapter', ctx.meta,
        Column('id', SmallInteger(unsigned=True), autoincrement=True,
               primary_key=True),
        Column('priority', TinylInteger(unsigned=True), nullable=False),
        Column('text', String(100), nullable=False)
    )

    ctx.tbl_topic = Table('topic', ctx.meta,
        Column('id', SmallInteger(unsigned=True), autoincrement=True,
               primary_key=True),
        Column('text', String(100), nullable=False),
        Column('text_fr', String(100), nullable=False),
        Column('text_de', String(100), nullable=False),
        Column('chapter_id', SmallInteger(unsigned=True),
               ForeignKey('chapter.id', onupdate='CASCADE', ondelete='CASCADE'))
    )

    ctx.tbl_questions = Table('questions', ctx.meta,
        Column('id', SmallInteger(unsigned=True), autoincrement=True,
               primary_key=True),
        Column('text', String(256), nullable=False),
        Column('text_fr', String(256)),
        Column('text_de', String(256)),
        Column('answer', Boolean, nullable=False),
        Column('image', String(10)),
        Column('image_part', String(10)),
        Column('chapter_id', SmallInteger(unsigned=True),
               ForeignKey('chapter.id', onupdate='CASCADE', ondelete='CASCADE')),
        Column('topic_id', SmallInteger(unsigned=True),
               ForeignKey('topic.id', onupdate='CASCADE', ondelete='CASCADE'))
    )


def fill_apps():
    print('Populating applications...')
    ctx.conn.execute(ctx.tbl_apps.insert(), APPLICATIONS)


def initdb():
    print('Initializing DB...')
    ctx.meta.drop_all(ctx.engine)
    ctx.meta.create_all(ctx.engine)
    fill_apps()


def create_users(user_type):
    import hashlib

    if user_type == 'real':
        users = REAL_USERS
    else:
        users = TEST_USERS

    def create_digest(username, passwd):
        m = hashlib.md5()
        m.update('%s:%s' % (username, passwd))
        return m.hexdigest()

    print('Creating test users...')
    vals = []
    for user in users:
        user['passwd'] = create_digest(user['login'], user['passwd'])
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
        ctx.conn.execute(ctx.tbl_chapter.insert(), lines)


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
        ctx.conn.execute(ctx.tbl_topic.insert(), lines)


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


if args.new:
    create_db()

if args.init or args.fill or args.users:
    prepare_db()

if args.init:
    initdb()

if args.users:
    create_users(args.users)

if args.fill:
    fill_chapters()
    fill_topics()
    fill_questions()
