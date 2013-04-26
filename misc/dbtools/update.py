"""
This module contains function for updating quiz db.
"""
import time
import traceback
from sqlalchemy import text
try:
    import simplejson as json
except ImportError:
    import json

engine = None
logger = None


def process(dbengine, log, clean):
    """Update statistics for all active schools."""
    global engine
    global logger
    engine = dbengine
    logger = log
    try:
        school_list = get_schools_for_update()
        if clean:
            do_clean(school_list)
        else:
            do_update(school_list)
    except:
        msg = traceback.format_exc()
        logger.critical(msg)


def do_update(school_list):
    logger.debug('Number of schools to update: %d', len(school_list))
    for school in school_list:
        start = time.time()
        logger.debug('Update school %d', school)
        update_school(school)
        end = time.time() - start
        logger.debug('Update school %d finished in %.3fs', school, end)
        time.sleep(1)


def get_schools_for_update():
    """Return list of schools for which update is needed."""
    res = engine.execute("""SELECT school_id FROM school_stat_cache WHERE
                         last_activity > last_update""")
    return [row[0] for row in res]


def update_school(school):
    """Update school statistics.

    The following data will be updated:
        * Guest visits (current, week, week3)
        * Students rating (current, week, week3)
        * Exams error percent (current, week, week3)
        * Topics statistics snapshot
    All collected data will be cached in the school_stat_cache table.
    """
    engine.execute(text("CALL update_school_snapshot(:id)"), id=school)

    stat = get_school_cache(school)
    students = get_active_students(school)
    if not students:
        return
    students_str = ','.join(str(user) for user in students)
    stat['guest_visits'] = get_guest_stat(school)
    stat['current'] = get_current_student_rating(students_str)
    stat['week'] = get_week_student_rating(students_str)
    stat['week3'] = get_week3_student_rating(students_str)
    stat['exams'] = get_exams_stat(students_str)
    stat = json.dumps(stat)
    engine.execute(text("""UPDATE school_stat_cache SET
                   last_update = UTC_TIMESTAMP(),
                   stat_cache=:cache WHERE school_id=:id
                   """), cache=stat, id=school)


def get_school_cache(school):
    """Return current school's statistics cache."""
    res = engine.execute(text("""SELECT stat_cache FROM school_stat_cache
                         WHERE school_id=:id"""), id=school).fetchone()
    try:
        data = json.loads(res[0])
    except Exception:
        data = {}
    return data


def get_active_students(school):
    """Return list of active students (last activity not less than 1 month)."""
    res = engine.execute(text("""SELECT
        id FROM users WHERE
        school_id=:id AND type='student' AND
        last_visit >= UTC_TIMESTAMP() - interval 30 day;
    """), id=school)
    return [int(row[0]) for row in res]


def get_guest_stat(school):
    """Return guest visit statistics as list [current, week, week3]."""
    # Find school's guest ID.
    res = engine.execute(text("""SELECT id FROM users WHERE
        school_id=:id AND type='guest'"""), id=school).fetchone()
    guest_id = res[0]

    # Get visit statistics
    res = engine.execute(text("""SELECT
        IFNULL((SELECT num_requests FROM guest_access_snapshot WHERE
         guest_id=:guest_id AND now_date=DATE(UTC_TIMESTAMP()) LIMIT 1), -1) c,
        IFNULL((SELECT ROUND(avg(num_requests)) FROM guest_access_snapshot WHERE
         guest_id=:guest_id AND
         now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 7 day
         AND DATE(UTC_TIMESTAMP()) - INTERVAL 1 DAY), -1) week,
        IFNULL((SELECT ROUND(avg(num_requests)) FROM guest_access_snapshot WHERE
         guest_id=:guest_id AND
         now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 21 day
         AND DATE(UTC_TIMESTAMP()) - interval 8 day), -1) week3;
        """), guest_id=guest_id).fetchone()

    return (res[0], res[1], res[2])


def get_current_student_rating(users_str):
    """Return list of best and worst students."""
    res = engine.execute("""SELECT id, name, surname, progress_coef FROM
        users WHERE id IN (%s) GROUP BY id ORDER by progress_coef DESC limit 3;
    """ % users_str)
    best = [{
        'id': row[0],
        'name': row[1],
        'surname': row[2],
        'coef': row[3]
    } for row in res if row[3] != -1]

    res = engine.execute("""SELECT id, name, surname, progress_coef FROM
        users WHERE id IN (%s) GROUP BY id ORDER by progress_coef limit 3;
    """ % users_str)
    worst = [{
        'id': row[0],
        'name': row[1],
        'surname': row[2],
        'coef': row[3]
    } for row in res if row[3] != -1]

    return {'best': best, 'worst': worst}


def get_users_info(res):
    data = {}
    users = []
    for row in res:
        data[row[0]] = row[1]
        users.append(str(row[0]))
    if not data:
        return []
    users = ','.join(users)
    res = engine.execute("""SELECT id, name, surname, progress_coef FROM
        users WHERE id IN (%s) ORDER by progress_coef""" % users)
    d = [{
        'id': row[0],
        'name': row[1],
        'surname': row[2],
        'coef': data[row[0]]
    } for row in res if data[row[0]] != -1]
    return d


def get_week_student_rating(users_str):
    """Return list of best and worst students."""
    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE
        user_id IN (%s) AND
        now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 7 day
        AND DATE(UTC_TIMESTAMP()) GROUP BY user_id ORDER by c DESC limit 3;
    """ % users_str)
    best = get_users_info(res)

    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE
        user_id IN (%s) AND
        now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 7 day
        AND DATE(UTC_TIMESTAMP()) GROUP BY user_id ORDER by c limit 3;
    """ % users_str)
    worst = get_users_info(res)

    return {'best': best, 'worst': worst}


def get_week3_student_rating(users_str):
    """Return list of best and worst students."""
    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE
        user_id IN (%s) AND
        now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 21 day
        AND DATE(UTC_TIMESTAMP()) - interval 8 day
        GROUP BY user_id ORDER by c DESC limit 3;
    """ % users_str)
    best = get_users_info(res)

    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE
        user_id IN (%s) AND
        now_date BETWEEN DATE(UTC_TIMESTAMP()) - interval 21 day
        AND DATE(UTC_TIMESTAMP()) - interval 8 day
        GROUP BY user_id ORDER by c limit 3;
    """ % users_str)
    worst = get_users_info(res)

    return {'best': best, 'worst': worst}


def get_exams_stat(users_str):
    """Return exams error percent list."""
    res = engine.execute("""SELECT
        (SELECT ROUND(SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100) e
         FROM exams WHERE user_id IN (%(u)s)) current,
        (SELECT ROUND(SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100) e
         FROM exams WHERE user_id IN (%(u)s) AND
         start_time BETWEEN DATE(UTC_TIMESTAMP()) - INTERVAL 7 DAY
         AND DATE(UTC_TIMESTAMP()) - INTERVAL 1 DAY) week,
        (SELECT ROUND(SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100) e
         FROM exams WHERE user_id IN (%(u)s) AND
         start_time BETWEEN DATE(UTC_TIMESTAMP()) - interval 21 day
         AND DATE(UTC_TIMESTAMP()) - INTERVAL 8 DAY) week3;
        """ % {'u': users_str}).fetchone()
    return (res[0], res[1], res[2])


###########################################################
# Cleanup functions
###########################################################

def do_clean(school_list):
    start = time.time()
    logger.debug('Cleanup started.')

    clean_schools_data()
    for school in school_list:
        clean_users_data(school)

    end = time.time() - start
    logger.debug('Cleanup finished in %.3fs', end)


def clean_schools_data():
    engine.execute("""DELETE FROM school_topic_err_snapshot
                   WHERE now_date < DATE(UTC_TIMESTAMP() - interval 30 day)""")

    engine.execute("""DELETE FROM guest_access_snapshot
                   WHERE now_date < DATE(UTC_TIMESTAMP() - interval 30 day)""")


# NONE: this will take long time.
# For 5000 users if takes ~4 min.
def clean_users_data(school):
    """Remove old history (older than 30 days)."""
    students = get_active_students(school)
    if not students:
        return
    students = ','.join(str(user) for user in students)

    engine.execute("""DELETE FROM user_progress_snapshot
                   WHERE now_date < DATE(UTC_TIMESTAMP() - interval 30 day)
                   AND user_id IN (%s)""" % students)

    engine.execute("""DELETE FROM topic_err_snapshot
                   WHERE now_date < DATE(UTC_TIMESTAMP() - interval 30 day)
                   AND user_id IN (%s)""" % students)

    engine.execute("""DELETE FROM exams
                   WHERE user_id IN (%s) AND end_time IS NULL
                   AND start_time < UTC_TIMESTAMP() - INTERVAL 3 HOUR
                   """ % students)
