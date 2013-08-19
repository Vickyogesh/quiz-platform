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
        logger.debug('Update school %s', str(school))
        update_school(school)
        end = time.time() - start
        logger.debug('Update school %s finished in %.3fs', str(school), end)
        time.sleep(1)


def get_schools_for_update():
    """Return list of schools for which update is needed."""
    return [{'id': 1, 'quiz_type': 1}]
    # res = engine.execute("""SELECT school_id, quiz_type FROM school_stat_cache
    #                      WHERE last_activity > last_update OR last_update = 0
    #                      """)
    # return [{'id': row[0], 'quiz_type': row[1]} for row in res]


def update_school(school):
    """Update school statistics.

    The following data will be updated:
        * Guest visits (current, week, week3)
        * Students rating (current, week, week3)
        * Exams error percent (current, week, week3)
        * Topics statistics snapshot
    All collected data will be cached in the school_stat_cache table.
    """
    engine.execute(text("CALL update_school_snapshot(:id, :type)"),
                   id=school['id'], type=school['quiz_type'])

    stat = get_school_cache(school)
    students = get_active_students(school)
    print students
    if not students:
        return
    students_str = ','.join(str(user) for user in students)
    qt = school['quiz_type']
    stat['guest_visits'] = get_guest_stat(school)
    stat['current'] = get_current_student_rating(students_str, qt)
    stat['week'] = get_week_student_rating(students_str, qt)
    stat['week3'] = get_week3_student_rating(students_str, qt)
    stat['exams'] = get_exams_stat(students_str, qt)
    stat = json.dumps(stat)
    engine.execute(text("""UPDATE school_stat_cache SET
                   last_update = UTC_TIMESTAMP(),
                   stat_cache=:cache WHERE school_id=:id AND quiz_type=:type
                   """), cache=stat, id=school['id'], type=qt)


def get_school_cache(school):
    """Return current school's statistics cache."""
    res = engine.execute(text("""SELECT stat_cache FROM school_stat_cache
                         WHERE school_id=:id AND quiz_type=:type"""),
                         id=school['id'], type=school['quiz_type']).fetchone()
    try:
        data = json.loads(res[0])
    except Exception:
        data = {}
    return data


def get_active_students(school):
    """Return list of active students (last activity not less than 1 month)."""
    res = engine.execute(text("""SELECT
        id FROM users WHERE
        school_id=:id AND type='student' AND quiz_type=:quiz_type AND
        last_visit >= UTC_TIMESTAMP() - interval 30 day;
    """), id=school['id'], quiz_type=school['quiz_type'])
    return [int(row[0]) for row in res]


def get_guest_stat(school):
    """Return guest visit statistics as list [current, week, week3]."""
    # Find school's guest ID.
    res = engine.execute(text("""SELECT id FROM users WHERE
        school_id=:id AND quiz_type=:type AND type='guest'"""),
                         id=school['id'], type=school['quiz_type']).fetchone()
    if res is None:
        return
    guest_id = res[0]

    # Get visit statistics
    res = engine.execute(text("""SELECT
        IFNULL((SELECT ROUND(avg(num_requests)) FROM guest_access_snapshot WHERE
         guest_id=:guest_id AND
         DATE(now_date) >  DATE(UTC_TIMESTAMP() - INTERVAL 2 DAY)), -1) c,
        IFNULL((SELECT ROUND(avg(num_requests)) FROM guest_access_snapshot WHERE
         guest_id=:guest_id AND
         DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 6 DAY)
         AND DATE(UTC_TIMESTAMP())), -1) week,
        IFNULL((SELECT ROUND(avg(num_requests)) FROM guest_access_snapshot WHERE
         guest_id=:guest_id AND
         DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 27 DAY)
         AND DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)), -1) week3;
        """), guest_id=guest_id).fetchone()

    return (res[0], res[1], res[2])


# def get_current_student_rating(users_str, quiz_type):
#     """Return list of best and worst students."""
#     res = engine.execute("""SELECT id, progress_coef FROM
#         users WHERE quiz_type=%d AND id IN (%s) GROUP BY id ORDER by progress_coef DESC limit 3;
#     """ % (quiz_type, users_str))
#     best = [{
#         'id': row[0],
#         'coef': row[1]
#     } for row in res if row[1] != -1]

#     res = engine.execute("""SELECT id, progress_coef FROM
#         users WHERE id IN (%s) GROUP BY id ORDER by progress_coef limit 3;
#     """ % users_str)
#     worst = [{
#         'id': row[0],
#         'coef': row[1]
#     } for row in res if row[1] != -1]

#     return {'best': best, 'worst': worst}


def get_users_info(res, quiz_type):
    data = {}
    users = []
    for row in res:
        data[row[0]] = row[1]
        users.append(str(row[0]))
    if not data:
        return []
    users = ','.join(users)
    res = engine.execute("""SELECT id, progress_coef FROM
        users WHERE quiz_type=%d AND id IN (%s) ORDER by progress_coef""" % (quiz_type, users))
    d = [{'id': row[0], 'coef': data[row[0]]}
         for row in res if data[row[0]] != -1]
    return d


def get_current_student_rating(users_str, quiz_type):
    """Return list of best and worst students."""
    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE quiz_type=%d AND
        user_id IN (%s) AND
        DATE(now_date) > DATE(UTC_TIMESTAMP() - INTERVAL 2 DAY)
        GROUP BY user_id ORDER by c DESC limit 3;
    """ % (quiz_type, users_str))
    best = get_users_info(res, quiz_type)

    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE quiz_type=%d AND
        user_id IN (%s) AND
        DATE(now_date) > DATE(UTC_TIMESTAMP() - INTERVAL 2 DAY)
        GROUP BY user_id ORDER by c limit 3;
    """ % (quiz_type, users_str))
    worst = get_users_info(res, quiz_type)

    return {'best': best, 'worst': worst}


def get_week_student_rating(users_str, quiz_type):
    """Return list of best and worst students."""
    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE quiz_type=%d AND
        user_id IN (%s) AND
        DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 6 DAY)
        AND DATE(UTC_TIMESTAMP()) GROUP BY user_id ORDER by c DESC limit 3;
    """ % (quiz_type, users_str))
    best = get_users_info(res, quiz_type)

    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE quiz_type=%d AND
        user_id IN (%s) AND
        DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 6 DAY)
        AND DATE(UTC_TIMESTAMP()) GROUP BY user_id ORDER by c limit 3;
    """ % (quiz_type, users_str))
    worst = get_users_info(res, quiz_type)

    return {'best': best, 'worst': worst}


def get_week3_student_rating(users_str, quiz_type):
    """Return list of best and worst students."""
    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE quiz_type=%d AND
        user_id IN (%s) AND
        DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 27 DAY)
        AND DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)
        GROUP BY user_id ORDER by c DESC limit 3;
    """ % (quiz_type, users_str))
    best = get_users_info(res, quiz_type)

    res = engine.execute("""SELECT user_id, avg(progress_coef) c
        FROM user_progress_snapshot WHERE quiz_type=%d AND
        user_id IN (%s) AND
        DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 27 DAY)
        AND DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)
        GROUP BY user_id ORDER by c limit 3;
    """ % (quiz_type, users_str))
    worst = get_users_info(res, quiz_type)

    return {'best': best, 'worst': worst}


def get_exams_stat(users_str, quiz_type):
    """Return exams error percent list."""
    res = engine.execute("""SELECT
        (SELECT ROUND(SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100) e
         FROM exams WHERE quiz_type=%(t)d AND user_id IN (%(u)s)) current,
        (SELECT ROUND(SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100) e
         FROM exams WHERE quiz_type=%(t)d AND user_id IN (%(u)s) AND
         DATE(start_time) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 6 DAY)
         AND DATE(UTC_TIMESTAMP())) week,
        (SELECT ROUND(SUM(IF(err_count > 4, 1, 0))/COUNT(end_time)*100) e
         FROM exams WHERE quiz_type=%(t)d AND user_id IN (%(u)s) AND
         DATE(start_time) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 27 DAY)
         AND DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)) week3;
        """ % {'u': users_str, 't': quiz_type}).fetchone()
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
    qt = school['quiz_type']

    engine.execute("""DELETE FROM user_progress_snapshot
                   WHERE now_date < DATE(UTC_TIMESTAMP() - interval 30 day)
                   AND user_id IN (%s) and quiz_type=%d""" % (students, qt))

    engine.execute("""DELETE FROM topic_err_snapshot
                   WHERE now_date < DATE(UTC_TIMESTAMP() - interval 30 day)
                   AND user_id IN (%s) and quiz_type=%d""" % (students, qt))

    engine.execute("""DELETE FROM exams
                   WHERE user_id IN (%s) AND end_time IS NULL
                   AND start_time < UTC_TIMESTAMP() - INTERVAL 3 HOUR
                   and quiz_type=%d
                   """ % (students, qt))
