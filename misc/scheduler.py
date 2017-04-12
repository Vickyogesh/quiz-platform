import os

from apscheduler.schedulers.blocking import BlockingScheduler


def db_update():
    os.system('python /var/www/quiz2/misc/dbupdate.py -v -l /var/log/dbupdate.log -c /var/www/quiz2/misc/config.ini')


def db_clean():
    os.system('python /var/www/quiz2/misc/dbupdate.py -v -l /var/log/dbupdate.log -c /var/www/quiz2/misc/config.ini --clean --force')
    os.system('python /var/www/quiz2/manage.py stat update')


def del_old_session():
    os.system('find /var/www/quiz2/data/sessions -mtime +1 -type f -exec rm {} \;')


def log_rotate():
    os.system('logrotate -f /etc/logrotate.d/nginx')

scheduler = BlockingScheduler()
# Turned off for development stage
# scheduler.add_job(db_update, 'interval', minutes=5)
# scheduler.add_job(db_clean, 'cron', day_of_week=6)
scheduler.add_job(del_old_session, 'cron', hour=2)
scheduler.add_job(log_rotate, 'cron', hour=10)

try:
    scheduler.start()
except (KeyboardInterrupt, SystemExit):
    pass