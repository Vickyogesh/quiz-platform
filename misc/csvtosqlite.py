# coding=utf-8
"""Convert CSV file with quiz to sqlite DB.

Expected CSV format:

par,a01,a02,cc,pc,afn,aft,fig,afc,senm,@sep,vf,tip

Columns description:
1 (par) is the topic name
2 (a01) is the chapter
3 (a02)
4-6 (cc,pc,afn)
7 (aft) is the question text
8-9 (fig,afc)
10 (senm) is the image id
11 (@sep)
12 (vf) is true/false, answer
13 (tip) only for truck quiz, list of sub licenses.

Expected input file encoding is UTF8.
Result db is used by dbfill.py script to put quiz to the MySQL db.
"""
from __future__ import print_function
import logging
import sqlite3
import csv
import argparse
import os.path
import sys
from collections import namedtuple

Item = namedtuple('Item', ['topic', 'chapter', 'text', 'image', 'answer'])

TOPIC = 0
CHAPTER = 1
TEXT = 2
IMAGE = 3
ANSWER = 4

areas = [
    ('Normativa sociale', (1, 2)),
    ('Disposizioni per il trasporto nazionale e internazionale', (3, 4)),
    ('Incidenti ed emergenza', (5, 6)),
    ('Masse, dimensioni dei veicoli e campo visivo', (7, 8)),
    ('Carico, aggancio e vari tipi di veicoli pesanti', (9, 10)),
    ('Tecnica e funzionamento del veicolo', (11, 12, 13, 14)),
    ('Manutenzione e guasti', (15, 16)),
    ('Responsabilità e contratto di trasporto', (17,))
]

parser = argparse.ArgumentParser(
    prog="csvtosqlite",
    description="Tool for converting CSV file with quiz to sqlite DB.")
parser.add_argument(
    '-o',
    help="Output dir (default: current working dir).",
    default='.',
    dest='out_dir')
parser.add_argument('input', metavar='INPUT',help="Input CSV file.")


def setup_db(out_file):
    if os.path.isfile(out_file):
        os.remove(out_file)
    conn = sqlite3.connect(out_file)

    c = conn.cursor()
    c.execute("CREATE TABLE chapters(title TEXT, priority INTEGER)")
    c.execute("CREATE TABLE topics(chapter_id INTEGER, title TEXT)")
    c.execute("""CREATE TABLE questions(topic_id INTEGER,
              chapter_id INTEGER, text TEXT, answer INTEGER, image TEXT,
              image_part TEXT, text_de TEXT, text_fr TEXT)""")
    conn.commit()
    return conn


def parse_csv(input_file):
    data = {}
    f = open(input_file, "rb")
    reader = csv.reader(f, delimiter=',')

    is_first = True
    for row in reader:
        if is_first:
            is_first = False
            continue

        item = [row[i].decode('utf8').strip() for i in (0, 1, 6, 9, 11)]
        item[CHAPTER] = int(item[CHAPTER].replace('.', ''))
        item[ANSWER] = 1 if item[ANSWER] == 'V' else 0
        item[IMAGE] = '' if not item[IMAGE] else int(item[IMAGE])
        item = Item._make(item)

        # sub license format: (X X X X)
        if len(row) > 12:
            txt = row[12][1:-1]
            sub_license = [int(x) for x in txt.split(' ')]
        else:
            sub_license = [0]

        for x in sub_license:
            put_item(data, x, item)

    return data


def get_or_create(name, src, cls=dict):
    d = src.get(name)
    if d is None:
        d = cls()
        src[name] = d
    return d


def put_item(data, sublicense, item):
    quiz = get_or_create(sublicense, data)
    chapters = get_or_create('chapters', quiz, list)
    topics = get_or_create('topics', quiz)
    questions = get_or_create('questions', quiz, list)

    if item.chapter not in chapters:
        chapters.append(item.chapter)
    if item.topic not in topics:
        topics[item.topic] = (item.chapter, len(topics))
    questions.append(item)


def write_data(quiz, out):
    logging.info('Creating %s...', out)
    chapters = quiz['chapters']
    topics = quiz['topics']
    questions = quiz['questions']

    conn = setup_db(out)
    c = conn.cursor()

    lst = [('Capitolo %d' % x, 1) for x in range(1, len(chapters) + 1)]
    c.executemany('INSERT INTO chapters VALUES(?,?)', lst)

    lst = [None] * len(topics)
    for txt, (ch, tid) in topics.iteritems():
        lst[tid] = (chapters.index(ch) + 1, txt)
    c.executemany('INSERT INTO topics VALUES(?,?)', lst)

    vals = []
    for q in questions:
        tinfo = topics[q.topic]
        assert tinfo[0] == q.chapter
        vals.append((tinfo[1] + 1, chapters.index(q.chapter) + 1, q.text,
                     q.answer, q.image, None, None, None))

    c.executemany('INSERT INTO questions VALUES(?,?,?,?,?,?,?,?)', vals)
    conn.commit()


logging.basicConfig(format='%(message)s', level=logging.DEBUG)
args = parser.parse_args()

data = parse_csv(args.input)

# for num, quiz in data.iteritems():
#     out = os.path.abspath('{0}/quizdb-{1}.sqlite'.format(args.out_dir, num))
#     write_data(quiz, out)

logging.info('Truck sub license areas:')

# -- truck sublicense areas ----------------------------------------------------
titles = []
chapters = []
for area in areas:
    titles.append(area[0])
    chapters.append(area[1])

for num, quiz in data.iteritems():
    area_info = {}
    ch = quiz['chapters']
    topics = quiz['topics']
    for c in ch:
        for area_chapters in chapters:
            if c in area_chapters:
                x = get_or_create(chapters.index(area_chapters), area_info, set)
                x.add(c)

    keys = sorted(area_info.keys())
    logging.info(num)
    for k in keys:
        v = sorted(list(area_info[k]))
        fixed = [x - ch[0] + 1 for x in v]

        items = []
        for c in v:
            ti = []
            for _, t in topics.iteritems():
                if t[0] == c:
                    ti.append(t[1] + 1)
            ti.sort()
            items.append(ti)

        logging.info("%s: %s %s", titles[k], fixed, items)
    logging.info("-" * 40)
