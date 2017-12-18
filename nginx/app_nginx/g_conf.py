import os, multiprocessing

bind = "127.0.0.1:8000"

if os.environ.get("PROD"):
    workers = multiprocessing.cpu_count() * 2 + 1
else:
    workers = 1

chdir = "/var/www/quiz2"
errorlog = "/var/log/g_errors.log"