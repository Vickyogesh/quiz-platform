from .settings import APPLICATIONS, TEST_SCHOOLS, TEST_USERS


def fill(mgr):
    fillApps(mgr)
    fillUsers(mgr)


def fillApps(mgr):
    print('Populating applications...')
    mgr.conn.execute(mgr.tbl_apps.insert(), APPLICATIONS)


def fillUsers(mgr):
    if not mgr.put_users:
        return
    print("Populating users...")
    vals = []
    for user in TEST_SCHOOLS:
        user['passwd'] = mgr._create_digest(user['login'], user['passwd'])
        vals.append(user)
    mgr.conn.execute(mgr.tbl_schools.insert(), vals)

    vals = []
    for user in TEST_USERS:
        user['passwd'] = mgr._create_digest(user['login'], user['passwd'])
        vals.append(user)
    mgr.conn.execute(mgr.tbl_users.insert(), vals)
