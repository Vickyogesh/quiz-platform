from .settings import APPLICATIONS


def fill(mgr):
    fillApps(mgr)


def fillApps(mgr):
    print('Populating applications...')
    mgr.conn.execute(mgr.tbl_apps.insert(), APPLICATIONS)
