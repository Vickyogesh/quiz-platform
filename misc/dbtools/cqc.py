import string
import os.path
from . import tables
from . import questions
from .settings import CQC

_mgr = None
_chid = 0
_tid = 0
_qid = 0


def run(mgr):
    print "Fill with CQC questions..."
    global _mgr
    global _chid
    global _tid
    global _qid
    _mgr = mgr
    _chid = 0
    _tid = 0
    _qid = 0

    tables.reflect(_mgr)
    pre_process()

    d = os.path.dirname(__file__)
    path = os.path.join(d, '..', 'dbdata', 'cqc.txt')
    parser(path, updater)
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


def parser(name, fn):
    chapter = ''
    txt = ''
    ans = ''
    items = []
    f = open(name, 'r')

    for line in f:
        row = line[:-1]
        if row[0] in string.digits and row[-1] == ')':
            if txt:
                items.append((chapter, ans, txt))
                fn(items)
            items = []
            chapter = int(row[:2])
            txt = ''
            ans = ''
            multiline = False
        elif row[0] in 'VF':
            if txt:
                items.append((chapter, ans, txt))
            ans = row[0] == 'V'
            multiline = row[-1] == ']'
            if multiline:
                txt = ''
                continue
            else:
                idx = row.find(']')
                txt = row[idx + 2:]
                # txt = row[idx + 2:].decode('utf-8')
        elif multiline:
            txt += row.decode('utf-8')
    items.append((chapter, ans, txt))
    fn(items)


def updater(items):
    global _chid
    global _tid
    global _qid

    t = _mgr.tbl_questions
    data = []

    for item in items:
        chapter_id = item[0]
        answer = item[1]
        text = item[2]

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


# def func(items):
#     c.executemany('INSERT INTO questions VALUES(?,?,?)', items)


# conn = sqlite3.connect('out.sqlite')
# c = conn.cursor()
# c.execute('CREATE TABLE IF NOT EXISTS questions(chapter, answer, question)')
# c.execute('DELETE FROM questions')
# parser('src.txt', func)
# conn.commit()
