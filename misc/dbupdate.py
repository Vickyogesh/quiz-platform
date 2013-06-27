"""
Tools to update quiz db.
"""
from __future__ import print_function
import argparse
import logging
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
import time
import traceback
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))
from sqlalchemy import create_engine
from quiz.settings import Settings
#from quiz.accounts import AccountApi
from dbtools import update

settings = None


def get_settings(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(__file__),
                            '..',
                            'test-data',
                            'config.ini')
        paths = os.path.split(os.path.abspath(path))
    else:
        paths = os.path.split(path)

    global settings
    Settings.CONFIG_FILE = paths[1]
    settings = Settings([paths[0]])


def get_engine():
    uri = settings.dbinfo['database']
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

get_settings(args.config)
# account = AccountApi(settings.main['accounts_url'])
# try:
#     login = settings.main['accounts_admin_login']
#     passwd = settings.main['accounts_admin_passwd']
#     account.login(login, passwd)
# except:
#     msg = traceback.format_exc()
#     logger.critical(msg)
# else:
engine = get_engine()
logger.info('Update started')
start = time.time()
update.process(engine, logger, args.clean)
end = time.time() - start
logger.info('Update finished in %.3fs', end)

engine.dispose()
#account.logout()
