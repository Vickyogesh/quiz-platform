# Script for creating quiz database from the CSV files.
# The following input is expected:
#   * chapters CSV
#   * topics CSV
#   * quiz questions CSV
from __future__ import print_function
import sqlite3
import csv
import argparse
import os.path
import sys


# Return dict with CSV files paths
def find_csv_files(in_dir):
    paths = {
        "chapters": os.path.join(in_dir, 'chapters.csv'),
        "topics": os.path.join(in_dir, 'topics.csv'),
        "questions": os.path.join(in_dir, 'questions.csv')
    }
    for k, v in paths.iteritems():
        if not os.path.isfile(v):
            print("Can't find %s" % os.path.abspath(v))
            sys.exit(1)
    return paths


def get_csv_items(path, cols):
    print("Processing %s" % os.path.basename(path))
    items = []
    is_first = True
    with open(path, "rb") as cfile:
        reader = csv.reader(cfile, delimiter='$')
        for row in reader:
            if is_first:
                is_first = False
                continue
            items.append([row[i].decode('utf8') for i in cols])
    return items


def setup_db(out_file):
    print("Setup %s" % os.path.basename(out_file))
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


def fill_chapters(csv_files, conn):
    items = get_csv_items(csv_files['chapters'], (0, 1))
    c = conn.cursor()
    c.executemany('INSERT INTO chapters VALUES(?,?)', items)
    conn.commit()


def fill_topics(csv_files, conn):
    items = get_csv_items(csv_files['topics'], (0, 1))
    c = conn.cursor()
    c.executemany('INSERT INTO topics VALUES(?,?)', items)
    conn.commit()


def fill_questions(csv_files, conn):
    items = get_csv_items(csv_files['questions'], (0, 1, 2, 3, 4, 5, 6, 7))
    for x in items:
        x[3] = 1 if x[3] == 'V' else 0
    c = conn.cursor()
    c.executemany('INSERT INTO questions VALUES(?,?,?,?,?,?,?,?)', items)
    conn.commit()


parser = argparse.ArgumentParser(
    prog="quizdb",
    description="Tool for creating quiz DB.")
parser.add_argument(
    '-o',
    help="Output database (default: %(default)s).",
    default='quiz.sqlite',
    dest='out_file')
parser.add_argument(
    '-i',
    help="Input dir with CSV files (default: current dir).",
    default=".",
    dest='in_dir')

args = parser.parse_args()
csv_files = find_csv_files(args.in_dir)
conn = setup_db(args.out_file)

fill_chapters(csv_files, conn)
fill_topics(csv_files, conn)
fill_questions(csv_files, conn)
