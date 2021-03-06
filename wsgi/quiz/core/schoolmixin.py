try:
    import simplejson as json
except ImportError:
    import json


class SchoolMixin(object):
    """This mixin provides school features. Used in QuizCore."""
    def __init__(self):
        self.__topics = self.sql("""SELECT t.id, t.text, t.text_fr, t.text_de,
        IFNULL((SELECT avg(err_percent)FROM school_topic_err_snapshot WHERE
           school_id=:school_id AND quiz_type=t.quiz_type AND topic_id = t.id
           AND DATE(now_date) = DATE(UTC_TIMESTAMP())),
           -1) current,

        IFNULL((SELECT avg(err_percent) FROM school_topic_err_snapshot WHERE
           school_id=:school_id AND quiz_type=t.quiz_type AND topic_id = t.id
           AND
           DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 7 DAY)
           AND DATE(UTC_TIMESTAMP() - INTERVAL 1 DAY)
           GROUP BY topic_id), -1) week,

        IFNULL((SELECT avg(err_percent) FROM school_topic_err_snapshot WHERE
           school_id=:school_id AND quiz_type=t.quiz_type AND topic_id = t.id
           AND
           DATE(now_date) BETWEEN DATE(UTC_TIMESTAMP() - INTERVAL 62 DAY)
           AND DATE(UTC_TIMESTAMP() - INTERVAL 8 DAY)
           GROUP BY topic_id), -1) week3
        FROM topics t WHERE quiz_type=:quiz_type;""")

        self.__cache = self.sql("""SELECT
            stat_cache FROM school_stat_cache WHERE school_id=:school_id
            AND quiz_type=:quiz_type""")

    def deleteStudent(self, id):
        t = self.users
        self.engine.execute(t.delete().where(t.c.id == id))

    def __getSchoolTopics(self, quiz_type, school_id, lang):
        if lang == 'de':
            lang = 3
        elif lang == 'fr':
            lang = 2
        else:
            lang = 1

        topics = []
        rows = self.__topics.execute(school_id=school_id, quiz_type=quiz_type)
        for row in rows:
            topics.append({
                'id': row[0],
                'text': row[lang],
                'errors': {
                    'current': self._normErr(row[4]),
                    'week': self._normErr(row[5]),
                    'week3': self._normErr(row[6])
                }
            })
        return topics

    def getSchoolStat(self, quiz_type, school_id, lang):
        """Aggregated school's statistics."""
        topics = self.__getSchoolTopics(quiz_type, school_id, lang)
        stat = self.__cache.execute(school_id=school_id, quiz_type=quiz_type)
        stat = stat.fetchone()

        try:
            stat = json.loads(stat[0])
            guest_visits = stat['guest_visits']
            if not guest_visits:
                guest_visits = [-1, -1, -1]
            data = {
                'topics': topics,
                'students': {
                    'current': stat['current'],
                    'week': stat['week'],
                    'week3': stat['week3']
                },
                'guest_visits': guest_visits,
                'exams': stat['exams']
            }
        except Exception:
            data = {
                'topics': topics,
                'students': {
                    'current': [],
                    'week': [],
                    'week3': []
                },
                'guest_visits': [-1, -1, -1],
                'exams': []
            }
        return data
