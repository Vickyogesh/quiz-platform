from flask_babelex import lazy_gettext

meta = {
    'am':
        {
            'name': 'am',
            'title': lazy_gettext('Scooter'),
            'exam_meta': {'max_errors': 3, 'total_time': 1500, 'num_questions': 30}
        },
    'b':
        {
            'name': 'b',
            'title': lazy_gettext('Quiz B'),
            'exam_meta': {'max_errors': 4, 'total_time': 1800, 'num_questions': 40}
        },
    'cde':
        {
            'title': {
                5: lazy_gettext('Licenses categories C1 - C1E'),
                6: lazy_gettext('Licenses categories C1 - C1E code Union 97'),
                7: lazy_gettext('Licenses categories C - CE'),
                8: lazy_gettext('Licenses categories C - CE formerly C1'),
                9: lazy_gettext('Licenses categories D1 - D1E'),
                10: lazy_gettext('Licenses categories D - DE'),
                11: lazy_gettext('Licenses categories D - DE formerly D1'),
            },
            'exam_meta': {
                5: {
                    'max_errors': 2,
                    'total_time': 1200,
                    'num_questions': 20,
                    'questions_per_chapter': [2, 3, 3, 1, 3, 1, 3, 1, 1, 2]
                },
                6: {
                    'max_errors': 1,
                    'total_time': 1200,
                    'num_questions': 10,
                    'questions_per_chapter': [2, 1, 3, 1, 1, 2]

                },
                7: {
                    'max_errors': 4,
                    'total_time': 2400,
                    'num_questions': 40,
                    'questions_per_chapter': [2, 3, 4, 1, 2, 1, 3, 1, 1, 2, 5, 1, 4, 3,
                                              3, 3, 1]

                },
                8: {
                    'max_errors': 2,
                    'total_time': 1200,
                    'num_questions': 20,
                    'questions_per_chapter': [5, 1, 4, 3, 3, 3, 1]

                },
                9: {
                    'max_errors': 2,
                    'total_time': 1200,
                    'num_questions': 20,
                    'questions_per_chapter': [2, 3, 2, 1, 2, 2, 3, 1, 2, 2]

                },
                10: {
                    'max_errors': 4,
                    'total_time': 2400,
                    'num_questions': 40,
                    'questions_per_chapter': [2, 3, 3, 1, 3, 2, 3, 1, 2, 2, 5, 1, 4, 2,
                                              3, 3]

                },
                11: {
                    'max_errors': 2,
                    'total_time': 1200,
                    'num_questions': 20,
                    'questions_per_chapter': [5, 2, 4, 3, 3, 3]

                }
            }
        },
    'cqc':
        {
            'name': 'cqc',
            'title': lazy_gettext('CQC'),
            'exam_meta': {'max_errors': 6, 'total_time': 7200, 'num_questions': 60}
        }

}


def get_quiz_meta(session):
    quiz_meta = meta.get(session['quiz_name'])

    # if exam has sublicenses
    if quiz_meta['exam_meta'].get(session['quiz_id']):
        # we replace title with sublicense title
        quiz_meta['title'] = quiz_meta['title'][session['quiz_id']]
        # and exam meta with sublicense meta
        quiz_meta['exam_meta'] = quiz_meta['exam_meta'].get(session['quiz_id'])
    return quiz_meta
