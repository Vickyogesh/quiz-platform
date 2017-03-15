import os

from apscheduler.schedulers.blocking import BlockingScheduler


def db_update():
    os.system('python /var/www/quiz2/misc/dbupdate.py -v -l /var/log/dbupdate.log -c /var/www/quiz2/misc/config.ini')

scheduler = BlockingScheduler()
# Turned off for development stage
# scheduler.add_job(db_update, 'interval', minutes=5)

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass