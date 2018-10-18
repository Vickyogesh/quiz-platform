import os
import sys
import requests
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'wsgi'))
from sqlalchemy import create_engine
from quiz.settings import Settings

engine = create_engine("{}{}".format(os.environ.get("DB_URI"), os.environ.get("DB_NAME")))

accounts_url = os.environ.get("ACCOUNTS_URL", "https://accounts.editricetoni.it/api/v1")

data = requests.get(accounts_url+"/inactive_students", headers={'X-Auth': 'xZM8L5Yv3NPMX6mg'}).json()

students = [str(s) for s in data['students']]

sql1 = "DELETE FROM users WHERE id IN ({})".format(",".join(students))

sql2 = "DELETE FROM users WHERE DATE(last_visit) < DATE (NOW() - INTERVAL {} DAY )".format(data.get('delete_period', 180))

engine.execute(sql1)
engine.execute(sql2)