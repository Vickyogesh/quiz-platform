from flask_babelex import lazy_gettext
from ..common.base import Bundle

quiz = Bundle(__name__, {
    'name': 'b',
    'title': lazy_gettext('Quiz B'),
    'exam_meta': {'max_errors': 4, 'total_time': 1800, 'num_questions': 40}
})
