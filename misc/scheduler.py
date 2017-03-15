import os

from apscheduler.schedulers.blocking import BlockingScheduler


def db_update():
    os.system('python /var/www/quiz2/misc/dbupdate.py -v -l /var/log/dbupdate.log -c /var/www/quiz2/misc/config.ini')


def del_old_session():
    os.system('find /var/www/quiz2/data/sessions -mtime +1 -type f -exec rm {} \;')

scheduler = BlockingScheduler()
# Turned off for development stage
# scheduler.add_job(db_update, 'interval', minutes=5)
scheduler.add_job(del_old_session, 'cron', hour=2)

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass