import os
from apscheduler.schedulers.blocking import BlockingScheduler

def cert_renew():
    os.system('certbot renew')

def log_rotate():
    os.system('logrotate -f /etc/logrotate.d/nginx')

scheduler = BlockingScheduler()
scheduler.add_job(cert_renew, 'cron', hour=2)
scheduler.add_job(log_rotate, 'interval', hours=12)

if __name__ == '__main__':
    scheduler.start()