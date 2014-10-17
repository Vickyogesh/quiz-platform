from flask import Blueprint, abort, Response, url_for
from flask.ext.assets import Bundle
from .. import assets
from ..login import QUIZ_ID_MAP

#NOTE: g.line.js has some changes/fixes.
ui = Blueprint('ui', __name__,
               template_folder='templates', static_folder='static',
               static_url_path='/static/ui')

# filters: yui_js, rjsmin, jsmin, cssmin, yui_css
js_filter = 'yui_js'
css_filter = 'yui_css'

base_js = Bundle('ui/js/libs/sprintf.min.js',
                 'ui/js/libs/jquery.colorbox-min.js',
                 'ui/js/libs/jquery.mousewheel.min.js',
                 'ui/js/libs/moment.min.js',
                 'ui/js/libs/moment.langs.js',
                 'ui/js/common.js', 'ui/js/expressbar.js',
                 'ui/js/fbsupport.js',
                 filters=js_filter, output='ui/gen/base.js')

bb_js = Bundle('ui/js/libs/json2.js', 'ui/js/libs/underscore-min.js',
               'ui/js/libs/backbone-min.js', 'ui/js/msgbox.js',
               'ui/js/dialog-bb.js', 'ui/js/quiz-model.js',
               'ui/js/quiz-menu.js',
               filters=js_filter, output='ui/gen/bb.js')

graph_js = Bundle('ui/js/libs/raphael-min.js',
                  'ui/js/libs/g.raphael-min.js',
                  'ui/js/libs/g.line.js', 'ui/js/libs/g.pie.js',
                  'ui/js/chart.js',
                  filters=js_filter, output='ui/gen/graph.js')

user_stat_js = Bundle('ui/js/stat-user.js', 'ui/js/stat-exam.js',
                      filters=js_filter, output='ui/gen/user-stat.js')

quiz_js = Bundle('ui/js/quiz-view.js', 'ui/js/quiz-review.js',
                 filters=js_filter, output='ui/gen/quiz.js')

exam_js = Bundle('ui/js/exam-model.js', 'ui/js/exam-view.js',
                 filters=js_filter, output='ui/gen/exam.js')

school_js = Bundle('ui/js/libs/md5.js', 'ui/js/school.js',
                   'ui/js/school-stat.js',
                   filters=js_filter, output='ui/gen/school.js')

css_ui = Bundle('ui/css/colorbox.css', 'ui/css/style.css',
                'ui/css/startup.css', 'ui/css/menu.css',
                'ui/css/statistics.css', 'ui/css/quiz.css',
                'ui/css/msgbox.css', 'ui/css/exam.css',
                'ui/css/school_menu.css', 'ui/css/school_stat.css',
                'ui/css/b_menu.css', 'ui/css/cqc_menu.css',
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
from . import util

school.register_views(ui)
client.register_views(ui)

@ui.route('/policy')
def policy():
    return util.render_template('ui/policy.html')


@ui.route('/<quiz_fullname>/aggiungi-piattaforma-a-pagina-facebook')
def fb_tab(quiz_fullname):
    if quiz_fullname not in QUIZ_ID_MAP:
        abort(404)
    tmpl = """<!DOCTYPE html>
    <html>
    <body>
    <script>top.location = "http://www.facebook.com/dialog/pagetab?app_id=306969962800273&redirect_uri={0}"</script>
    </body>
    </html>
    """.format(url_for('.index', quiz_fullname=quiz_fullname, fblogin=1,
                       _external=True))
    return Response(tmpl, mimetype='text/html')
