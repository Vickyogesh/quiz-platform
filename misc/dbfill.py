# Script to fill quiz db with questions from sqlite source.
from __future__ import print_function
import argparse
import os
import os.path
import sqlite3
import sys
import time
import traceback
from collections import namedtuple

# to use settings
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))

from sqlalchemy import create_engine, MetaData
from quiz.settings import Settings


DbData = namedtuple('DbData', ['engine', 'meta', 'conn',
                    'chapters', 'topics', 'questions'])


def create_db_data(config_path, verbose):
    if config_path is None:
        config_path = os.path.join(os.path.dirname(__file__), '..',
                                   'test-data', 'config.ini')
        paths = os.path.split(os.path.abspath(config_path))
    else:
        paths = os.path.split(config_path)

    Settings.CONFIG_FILE = paths[1]
    settings = Settings([paths[0]])
    engine = create_engine(settings.dbinfo['database'], echo=verbose)
    meta = MetaData()
    meta.reflect(bind=engine)
    conn = engine.connect()
    c = meta.tables['chapters']
    t = meta.tables['topics']
    q = meta.tables['questions']
    return DbData(engine, meta, conn, c, t, q)


def create_helper_func(db):
    db.conn.execute('DROP PROCEDURE IF EXISTS set_chapters_info;')
    db.conn.execute("""CREATE PROCEDURE set_chapters_info(IN type INT)
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

    db.conn.execute('DROP PROCEDURE IF EXISTS set_topics_info;')
    db.conn.execute("""CREATE PROCEDURE set_topics_info(IN type INT)
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


def pre_process(db, quiz_type, renew):
    print("Pre processing...")
    if renew:
        ch = db.chapters
        tp = db.topics
        q = db.questions
        db.conn.execute(ch.delete().where(ch.c.quiz_type == quiz_type))
        db.conn.execute(tp.delete().where(tp.c.quiz_type == quiz_type))
        db.conn.execute(q.delete().where(q.c.quiz_type == quiz_type))
    create_helper_func(db)


def post_process(db, quiz_type):
    print("Post processing...")
    db.conn.execute('CALL set_chapters_info(%d);' % quiz_type)
    db.conn.execute('CALL set_topics_info(%d);' % quiz_type)
    db.conn.execute('DROP PROCEDURE IF EXISTS set_chapters_info;')
    db.conn.execute('DROP PROCEDURE IF EXISTS set_topics_info;')
    # for tbl in db.meta.tables:
    #     print("Table optimizations... %s" % tbl)
    #     db.conn.execute('OPTIMIZE TABLE %s;' % tbl)


def fill(db, quiz_type, infile):
    if not os.path.exists(infile):
        raise IOError('File not found: %s' % infile)

    conn = sqlite3.connect(infile)
    c = conn.cursor()

    fill_chapters(db, quiz_type, c)
    fill_topics(db, quiz_type, c)
    fill_questions(db, quiz_type, c)


def fill_chapters(db, quiz_type, cur):
    print('--> chapters')

    Row = namedtuple('Row', ['rowid', 'title', 'priority'])
    cur.execute('SELECT %s FROM chapters' % ','.join(Row._fields))

    vals = [{
            'id': row.rowid,
            'quiz_type': quiz_type,
            'priority': row.priority,
            'text': row.title}
            for row in map(Row._make, cur)]

    db.conn.execute(db.chapters.insert(), vals)


def fill_topics(db, quiz_type, cur):
    print('--> topics')

    Row = namedtuple('Row', ['rowid', 'chapter_id', 'title'])
    cur.execute('SELECT %s FROM topics' % ','.join(Row._fields))

    vals = [{
            'id': row.rowid,
            'quiz_type': quiz_type,
            'text': row.title,
            'chapter_id': row.chapter_id}
            for row in map(Row._make, cur)]

    db.conn.execute(db.topics.insert(), vals)


def fill_questions(db, quiz_type, cur):
    print('--> questions')

    Row = namedtuple('Row', ['rowid', 'chapter_id', 'topic_id',
                     'text', 'text_fr', 'text_de', 'answer', 'image',
                     'image_part'])
    cur.execute('SELECT %s FROM questions' % ','.join(Row._fields))

    vals = [{
            'id': row.rowid,
            'quiz_type': quiz_type,
            'text': row.text,
            'text_fr': row.text_fr,
            'text_de': row.text_de,
            'answer': row.answer,
            'image': row.image,
            'image_part': row.image_part,
            'chapter_id': row.chapter_id,
            'topic_id': row.topic_id}
            for row in map(Row._make, cur)]

    db.conn.execute(db.questions.insert(), vals)


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Quiz database populate tool.', epilog='''
    Example:

        dbfill.py -t 3 -i dbdata/some.sqlite

    Opeshift note: you can found input files in the

        $OPENSHIFT_DATA_DIR/quiz/db_sources
    ''')

parser.add_argument('-v', '--verbose', action='store_true',
                    help='Verbose output.')
parser.add_argument('-c', '--config', default=None,
                    help="""Configuration file
                    (default: ../test-data/config.ini).""")
parser.add_argument('-r', '--renew', action='store_true',
                    help='Remove old data with the same type before filling.')
parser.add_argument('-t', '--type', type=int, required=True,
                    help='Quiz type (number).')
parser.add_argument('-i', '--input', required=True,
                    help="Input sqlite database.")
args = parser.parse_args()


start_time = time.time()
msg = ''
db = create_db_data(args.config, args.verbose)
t = db.conn.begin()

try:
    pre_process(db, args.type, args.renew)
    fill(db, args.type, args.input)
    post_process(db, args.type)
except Exception:
    traceback.print_exc()
    t.rollback()
    msg = '[Interrupted] '
except:
    t.rollback()
    msg = '[Interrupted] '
else:
    t.commit()
db.conn.close()
db.engine.dispose()
print('{0}Finished in ~{1:.2f}s'.format(msg, time.time() - start_time))
