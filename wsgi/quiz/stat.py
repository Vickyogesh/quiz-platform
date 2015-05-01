from datetime import datetime, timedelta
from collections import namedtuple
from sqlalchemy import select, desc
from sqlalchemy import func
from flask import current_app, json
from flask_script import Manager

Statistics = Manager(usage='Manage quiz statistics.')


Row = namedtuple('Row', ['quiz_type', 'school_id', 'finished',
                         'not_finished', 'err_count'])


def fill_exam_stat(stat, result, range_key, quiz_type_names):
    for row in result:
        row = Row(*row)

        # detect quiz name, with one exception. IDs 5 - 11 belongs to cde
        # See quiz.login.QUIZ_ID_MAP.
        if 5 <= row.quiz_type <= 11:
            quiz_name = 'cde'
        else:
            quiz_name = quiz_type_names[row.quiz_type]

        data = stat.setdefault(row.school_id, {}).setdefault(quiz_name, {})
        range_data = data.setdefault(range_key, {})
        range_data['finished'] = row.finished
        range_data['not_finished'] = row.not_finished
        range_data['err_count'] = row.err_count

@Statistics.command
def update():
    """Update schools exams statistics."""
    from quiz.login import QUIZ_ID_MAP
    quiz_type_names = dict(zip(QUIZ_ID_MAP.values(), QUIZ_ID_MAP.keys()))
    core = current_app.core
    stat_json = core.stat_json
    u = core.users
    e = core.exams

    # SELECT
    #     exams.quiz_type quiz_type,
    #     school_id,
    #     SUM(IF(end_time, 1, 0)) finished,
    #     SUM(IF(end_time, 0, 1)) not_finished,
    #     COUNT(user_id) num_exams,
    #     ROUND(AVG(IF(end_time, err_count, NULL))) err_count
    # FROM exams, users WHERE
    #     start_time >= DATE_SUB(DATE(UTC_TIMESTAMP()), INTERVAL 28 DAY) AND
    #     start_time < DATE_ADD(DATE(UTC_TIMESTAMP), INTERVAL 1 DAY)
    # AND users.id=user_id GROUP BY quiz_type, school_id
    # ORDER BY quiz_type, finished DESC, not_finished DESC;
    finished = func.sum(func.if_(e.c.end_time, 1, 0)).label('finished')
    not_finished = func.sum(func.if_(e.c.end_time, 0, 1)).label('not_finished')
    sql = select([
        e.c.quiz_type,
        u.c.school_id,
        finished,
        not_finished,
        func.round(func.avg(func.if_(e.c.end_time, e.c.err_count, None))).label('err_count')
    ])
    sql = sql.where(e.c.user_id == u.c.id)
    sql = sql.group_by(e.c.quiz_type, u.c.school_id)
    sql = sql.order_by(e.c.quiz_type, desc(finished), desc(not_finished))
    sql = sql.where(e.c.start_time < datetime.utcnow() + timedelta(days=1))

    sql_month = sql.where(e.c.start_time >= datetime.utcnow() - timedelta(days=28))
    sql_week = sql.where(e.c.start_time >= datetime.utcnow() - timedelta(days=7))

    stat = {'update_date': datetime.utcnow().isoformat()}
    fill_exam_stat(stat, core.engine.execute(sql_month), 'month',
                   quiz_type_names)
    fill_exam_stat(stat, core.engine.execute(sql_week), 'week',
                   quiz_type_names)

    add_str = "ON DUPLICATE KEY UPDATE value=VALUES(value)"
    sql = stat_json.insert(append_string=add_str)
    core.engine.execute(sql, {'name': 'exams', 'value': json.dumps(stat)})
