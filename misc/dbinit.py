#!/usr/bin/env python
''' Script for setup Quiz databse. '''

from __future__ import print_function
import os
import os.path

import argparse
import csv
from dbtools import DbManager
from dbtools.settings import QUIZ_B


# Input files
CHAPTERS_FILE = "dbdata/chapters.csv"
TOPICS_FILE = "dbdata/topics.csv"
QUESTIONS_FILE = "dbdata/questions.csv"


class Db(DbManager):
    def __init__(self):
        self.parseArgs()
        DbManager.__init__(self,
                           self.args.verbose,
                           self.args.config)

    def parseArgs(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Quiz databse setup tool.', epilog='''
            Examples.
            Recreate tables and fill them with data:
                    dbsetup.py -c config.ini

            NOTE: To recreate tables, fill them with data just run: dbsetup.py
            ''')
        parser.add_argument('-v', '--verbose', action='store_true',
                            help='Verbose output.')
        parser.add_argument('-c', '--config', default=None,
                            help="""Configuration file
                            (default: ../test-data/config.ini).""")
        parser.add_argument('-d', '--delimiter', default=',',
                            help="CSV delimiter (default: '%(default)s').")
        parser.add_argument('-cqc', action='store_true',
                            help="Fill with CQC questions.")
        self.args = parser.parse_args()

    def fillChapters(self):
        print('Populating chapters...')
        path = os.path.join(os.path.dirname(__file__), CHAPTERS_FILE)
        with open(path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.args.delimiter)
            lines = []
            is_first = True
            id = 1
            for row in reader:
                if is_first:
                    is_first = False
                    continue
                lines.append({'id': id, 'quiz_type': QUIZ_B, 'priority': row[2], 'text': row[1]})
                id += 1
            self.conn.execute(self.tbl_chapters.insert(), lines)

    def fillTopics(self):
        print('Populating topics...')
        path = os.path.join(os.path.dirname(__file__), TOPICS_FILE)
        with open(path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.args.delimiter)
            lines = []
            is_first = True
            id = 1
            for row in reader:
                if is_first:
                    is_first = False
                    continue
                text = row[1]
                text_fr = row[4] or text
                text_de = row[5] or text
                lines.append({
                    'id': id,
                    'quiz_type': QUIZ_B,
                    'text': text,
                    'text_fr': text_fr,
                    'text_de': text_de,
                    'chapter_id': row[2]
                })
                id += 1
            self.conn.execute(self.tbl_topics.insert(), lines)

    def fillQuestions(self):
        print('Populating questions...')
        path = os.path.join(os.path.dirname(__file__), QUESTIONS_FILE)
        with open(path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.args.delimiter)
            lines = []
            is_first = True
            id = 1
            for row in reader:
                if is_first:
                    is_first = False
                    continue
                lines.append({
                    'id': id,
                    'quiz_type': QUIZ_B,
                    'text': row[7],
                    'text_fr': row[11],
                    'text_de': row[12],
                    'answer': row[8] == 'V',
                    'image': row[9],
                    'image_part': row[10],
                    'chapter_id': row[1],
                    'topic_id': row[4]
                })
                id += 1
            self.conn.execute(self.tbl_questions.insert(), lines)

    def fillData(self):
        self.fillChapters()
        self.fillTopics()
        self.fillQuestions()

    def _do_run(self):
        if self.args.cqc:
            from dbtools import cqc
            cqc.run(self)
        else:
            DbManager._do_run(self)


Db().run()
