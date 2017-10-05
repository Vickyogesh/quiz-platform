import os
from apscheduler.schedulers.blocking import BlockingScheduler

def cert_renew():
    os.system('certbot renew')

scheduler = BlockingScheduler()
scheduler.add_job(cert_renew, 'cron', hour=2)

if __name__ == '__main__':
    scheduler.start()