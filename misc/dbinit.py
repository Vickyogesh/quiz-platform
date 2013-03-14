#!/usr/bin/env python
''' Script for setup Quiz databse. '''

from __future__ import print_function
import os
import os.path

import argparse
import csv
from dbtools import DbTool


# Input files
CHAPTERS_FILE = "dbdata/chapters.csv"
TOPICS_FILE = "dbdata/topics.csv"
QUESTIONS_FILE = "dbdata/questions.csv"


class Db(DbTool):
    def __init__(self):
        self.parseArgs()
        DbTool.__init__(self,
                        self.args.verbose,
                        self.args.new,
                        self.args.config)

        if self.args.test_users:
            self._users = DbTool.TEST_USERS

    def parseArgs(self):
        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description='Quiz databse setup tool.', epilog='''
            Examples.
            Setup database on a clean system with real users
            and populate with data:
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
        parser.add_argument('-c', '--config', default=None,
                            help="""Configuration file
                            (default: ../test-data/config.ini).""")
        parser.add_argument('-n', '--new', action='store_true',
                            help='Create quiz database.')
        parser.add_argument('-t', '--test-users', action='store_true',
                            help='Initialize with test users instead of real.')
        parser.add_argument('-d', '--delimiter', default=',',
                            help="CSV delimiter (default: '%(default)s').")
        self.args = parser.parse_args()

    def fillChapters(self):
        print('Populating chapters...')
        path = os.path.join(os.path.dirname(__file__), CHAPTERS_FILE)
        with open(path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.args.delimiter)
            lines = []
            is_first = True
            for row in reader:
                if is_first:
                    is_first = False
                    continue
                lines.append({'priority': row[2], 'text': row[1]})
            self.conn.execute(self.tbl_chapters.insert(), lines)

    def fillTopics(self):
        print('Populating topics...')
        path = os.path.join(os.path.dirname(__file__), TOPICS_FILE)
        with open(path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.args.delimiter)
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
            self.conn.execute(self.tbl_topics.insert(), lines)

    def fillQuestions(self):
        print('Populating questions...')
        path = os.path.join(os.path.dirname(__file__), QUESTIONS_FILE)
        with open(path, "rb") as csvfile:
            reader = csv.reader(csvfile, delimiter=self.args.delimiter)
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
            self.conn.execute(self.tbl_questions.insert(), lines)

    def fillData(self):
        self.fillChapters()
        self.fillTopics()
        self.fillQuestions()


Db().run()
