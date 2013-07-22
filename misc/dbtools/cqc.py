import string
import os.path
import sqlite3
from . import tables
from . import questions
from .settings import CQC

_mgr = None


def run(mgr):
    print "Fill with CQC questions..."
    global _mgr
    _mgr = mgr

    tables.reflect(_mgr)
    pre_process()
    do_fill()
    post_process()


def pre_process():
    ch = _mgr.tbl_chapters
    tp = _mgr.tbl_topics
    q = _mgr.tbl_questions

    _mgr.engine.engine.execute(ch.delete().where(ch.c.quiz_type == CQC))
    _mgr.engine.engine.execute(tp.delete().where(tp.c.quiz_type == CQC))
    _mgr.engine.engine.execute(q.delete().where(q.c.quiz_type == CQC))


def post_process():
    questions.create_func(_mgr)
    _mgr.engine.execute('CALL set_chapters_info(2);')
    _mgr.engine.execute('CALL set_topics_info(2);')
    _mgr.engine.execute('DROP PROCEDURE IF EXISTS set_chapters_info;')
    _mgr.engine.execute('DROP PROCEDURE IF EXISTS set_topics_info;')
    tables.do_optimize(_mgr)


def do_fill():
    db = os.path.dirname(__file__)
    db = os.path.join(db, '..', 'dbdata', 'cqc.sqlite')
    conn = sqlite3.connect(db)
    c = conn.cursor()
    c.execute('SELECT * FROM questions')

    _chid = 0
    _tid = 0
    _qid = 0
    t = _mgr.tbl_questions
    data = []
    for row in c:
        chapter_id = row[0]
        answer = row[1]
        text = row[2]

        _qid += 1
        if _chid != chapter_id:
            _chid = chapter_id
            _tid += 1

            ch = _mgr.tbl_chapters
            tp = _mgr.tbl_topics
            _mgr.engine.execute(ch.insert(), id=_chid, quiz_type=CQC,
                                priority=1, text='Chaptilo %d' % _chid)
            _mgr.engine.execute(tp.insert(), id=_tid, quiz_type=CQC,
                                text='Topic %d.1' % _chid, chapter_id=_chid)

        data.append({
            'id': _qid,
            'quiz_type': CQC,
            'text': text,
            'answer': answer,
            'chapter_id': _chid,
            'topic_id': _tid
        })

    _mgr.engine.execute(t.insert(), data)
    conn.close()
