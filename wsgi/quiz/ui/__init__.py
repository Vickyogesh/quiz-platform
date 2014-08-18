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

base_js = Bundle('ui/base/js/libs/sprintf.min.js',
                 'ui/base/js/libs/jquery.colorbox-min.js',
                 'ui/base/js/libs/jquery.mousewheel.min.js',
                 'ui/base/js/common.js', 'ui/base/js/expressbar.js',
                 'ui/base/js/fbsupport.js',
                 filters=js_filter, output='ui/gen/base.js')

bb_js = Bundle('ui/base/js/libs/json2.js', 'ui/base/js/libs/underscore-min.js',
               'ui/base/js/libs/backbone-min.js', 'ui/base/js/msgbox.js',
               'ui/base/js/dialog-bb.js', 'ui/base/js/quiz-model.js',
               filters=js_filter, output='ui/gen/bb.js')

graph_js = Bundle('ui/base/js/libs/raphael-min.js',
                  'ui/base/js/libs/g.raphael-min.js',
                  'ui/base/js/libs/g.line.js', 'ui/base/js/libs/g.pie.js',
                  'ui/base/js/chart.js',
                  filters=js_filter, output='ui/gen/graph.js')

user_stat_js = Bundle('ui/base/js/stat-user.js', 'ui/base/js/stat-exam.js',
                      filters=js_filter, output='ui/gen/user-stat.js')

quiz_js = Bundle('ui/base/js/quiz-topicslider.js',
                 'ui/base/js/quiz-view.js', 'ui/base/js/quiz-review.js',
                 filters=js_filter, output='ui/gen/quiz.js')

exam_js = Bundle('ui/base/js/exam-model.js', 'ui/base/js/exam-view.js',
                 filters=js_filter, output='ui/gen/exam.js')

school_js = Bundle('ui/base/js/libs/md5.js', 'ui/base/js/school.js',
                   'ui/base/js/school-stat.js',
                   filters=js_filter, output='ui/gen/school.js')

css_ui = Bundle('ui/base/css/colorbox.css', 'ui/base/css/style.css',
                'ui/base/css/startup.css', 'ui/base/css/menu.css',
                'ui/base/css/statistics.css', 'ui/base/css/quiz.css',
                'ui/base/css/msgbox.css', 'ui/base/css/exam.css',
                'ui/base/css/school_menu.css', 'ui/base/css/school_stat.css',
                filters=css_filter, output='ui/gen/ui.css')

assets.register('base.js', base_js)
assets.register('bb.js', bb_js)
assets.register('graph.js', graph_js)
assets.register('user-stat.js', user_stat_js)
assets.register('quiz.js', quiz_js)
assets.register('exam.js', exam_js)
assets.register('school.js', school_js)
assets.register('ui.css', css_ui)

from . import babel
from . import index
from . import school
from . import client

school.register_urls_for(ui)
client.register_urls_for(ui)
