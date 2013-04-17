"""
Tools to update quiz db.
"""
from __future__ import print_function
import argparse
import logging
import time
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))
from sqlalchemy import create_engine
from quiz.settings import Settings
from dbtools import update


def get_db_uri(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__),
                            '..',
                            'test-data',
                            'config.ini')
        paths = os.path.split(os.path.abspath(path))
    else:
        paths = os.path.split(path)

    Settings.CONFIG_FILE = paths[1]
    settings = Settings([paths[0]])
    return settings.dbinfo['database']


def get_engine(path):
    uri = get_db_uri(path)
    engine = create_engine(uri)
    return engine


parser = argparse.ArgumentParser(
    formatter_class=argparse.RawDescriptionHelpFormatter,
    description='Quiz databse update tool.', epilog='''''')
parser.add_argument('-v', '--verbose', action='store_true',
                    help="Verbose logging.")
parser.add_argument('-l', '--log', default=None, help="Log path.")
parser.add_argument('-c', '--config', default=None,
                    help="""Configuration file
                    (default: ../test-data/config.ini).""")
parser.add_argument('--clean', action='store_true', help="Cleanup db.")
args = parser.parse_args()

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s',
                    datefmt='%d.%m.%Y %H:%M:%S',
                    filename=args.log,
                    level=args.verbose and logging.DEBUG or logging.INFO)

engine = get_engine(args.config)

logging.info('Update started')
start = time.time()
update.process(engine, args.clean)
end = time.time() - start
logging.info('Update finished in %.3fs', end)

engine.dispose()
