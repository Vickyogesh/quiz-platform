"""
Tools to update quiz db.
"""
from __future__ import print_function
import argparse
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
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

# Logging setup
logger = logging.getLogger('dbupdate')
logger.setLevel(args.verbose and logging.DEBUG or logging.INFO)

fmt = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s',
                        '%d.%m.%Y %H:%M:%S')

if args.log:
    # Max log size is 5Mb
    handler = RotatingFileHandler(args.log, maxBytes=5242880, backupCount=1)
else:
    handler = StreamHandler()
handler.setFormatter(fmt)
logger.addHandler(handler)

engine = get_engine(args.config)

logger.info('Update started')
start = time.time()
update.process(engine, logger, args.clean)
end = time.time() - start
logger.info('Update finished in %.3fs', end)

engine.dispose()
