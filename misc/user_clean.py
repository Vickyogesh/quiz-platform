from os import environ
from sqlalchemy import create_engine

SQLALCHEMY_DATABASE_URI = "%s%s?charset=utf8" % (environ.get('DB_URI'), environ.get('DB_NAME'))

engine = create_engine(SQLALCHEMY_DATABASE_URI)


def remove_old_users():
    engine.execute("DELETE FROM users WHERE last_visit < DATE_SUB(CURDATE(), INTERVAL 6 MONTH)")

if __name__ == '__main__':
    remove_old_users()