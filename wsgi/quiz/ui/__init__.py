from flask import Blueprint
from flask.ext.assets import Bundle
from .. import assets

#NOTE: g.line.js has some changes/fixes.
ui = Blueprint('ui', __name__,
               template_folder='templates', static_folder='static',
               static_url_path='/static/ui')

# filters: yui_js, rjsmin, jsmin, cssmin, yui_css
js_filter = 'yui_js'
css_filter = 'yui_css'

base = ['ui/js/libs/sprintf.min.js', 'ui/js/libs/jquery.colorbox-min.js',
        'ui/js/libs/jquery.mousewheel.min.js', 'ui/js/common.js',
        'ui/js/expressbar.js']

base_js = Bundle(*base, filters=js_filter, output='ui/gen/base.js')

statistics_js = Bundle('ui/js/libs/raphael-min.js',
                       'ui/js/libs/g.raphael-min.js',
                       'ui/js/libs/g.line.js', 'ui/js/libs/g.pie.js',
                       'ui/js/libs/moment.min.js',
                       # ours
                       'ui/js/chart.js', 'ui/js/stat-user.js',
                       'ui/js/stat-exam.js',
                       filters=js_filter, output='ui/gen/stat.js')

quiz_js = Bundle('ui/js/libs/json2.js', 'ui/js/libs/underscore-min.js',
                 'ui/js/libs/backbone-min.js',
                 # ours
                 'ui/js/msgbox.js', 'ui/js/quiz-model.js',
                 'ui/js/quiz-topicslider.js',
                 'ui/js/quiz-view.js', 'ui/js/quiz-review.js',
                 filters=js_filter, output='ui/gen/quiz.js')

css_ui = Bundle('ui/css/colorbox.css', 'ui/css/style.css', 'ui/css/startup.css',
                'ui/css/menu.css', 'ui/css/statistics.css',
                'ui/css/quiz.css', 'ui/css/msgbox.css',
                filters=css_filter, output='ui/gen/ui.css')

assets.register('base.js', base_js)
assets.register('stat.js', statistics_js)
assets.register('quiz.js', quiz_js)
assets.register('ui.css', css_ui)

from . import babel
from . import index
from . import menu
from . import quiz
from . import statistics
