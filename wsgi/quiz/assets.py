from flask_assets import Bundle, Environment

assets = Environment()

# filters: yui_js, rjsmin, jsmin, cssmin, yui_css
js_filter = 'yui_js'
css_filter = 'yui_css'

base_js = Bundle('js/libs/sprintf.min.js',
                 'js/libs/jquery.colorbox-min.js',
                 'js/libs/jquery.mousewheel.min.js',
                 'js/libs/moment.min.js',
                 'js/libs/moment.langs.js',
                 'js/common.js', 'js/expressbar.js',
                 'js/fbsupport.js', 'js/libs/loggly.tracker-2.2.2.min.js',
                 filters=js_filter, output='gen/base.js')

bb_js = Bundle('js/libs/json2.js', 'js/libs/underscore-min.js',
               'js/libs/backbone-min.js', 'js/msgbox.js',
               'js/dialog-bb.js', 'js/quiz-model.js',
               'js/quiz-menu.js',
               filters=js_filter, output='gen/bb.js')

graph_js = Bundle('js/libs/raphael-min.js',
                  'js/libs/g.raphael-min.js',
                  'js/libs/g.line.js', 'js/libs/g.pie.js',
                  'js/chart.js',
                  filters=js_filter, output='gen/graph.js')

user_stat_js = Bundle('js/stat-user.js', 'js/stat-exam.js',
                      filters=js_filter, output='gen/user-stat.js')

quiz_js = Bundle('js/quiz-view.js', 'js/quiz-review.js',
                 filters=js_filter, output='gen/quiz.js')

exam_js = Bundle('js/exam-model.js', 'js/exam-view.js',
                 filters=js_filter, output='gen/exam.js')

school_js = Bundle('js/libs/md5.js', 'js/school.js',
                   'js/school-stat.js',
                   filters=js_filter, output='gen/school.js')

fullscreen_js = Bundle('js/fullscreen.js', filters=js_filter,
                       output='gen/fullscreen.js')

cm_js = Bundle('js/cm.js', filters=js_filter,
               output='gen/cm.js')

css_ui = Bundle('css/colorbox.css', 'css/style.css',
                'css/startup.css', 'css/menu.css',
                'css/statistics.css', 'css/quiz.css',
                'css/msgbox.css', 'css/exam.css',
                'css/school_menu.css', 'css/school_stat.css',
                'css/b_menu.css', 'css/cqc_menu.css',
                'css/fullscreen.css', 'css/cm.css',
                filters=css_filter, output='gen/ui.css')

assets.register('base.js', base_js)
assets.register('bb.js', bb_js)
assets.register('graph.js', graph_js)
assets.register('user-stat.js', user_stat_js)
assets.register('quiz.js', quiz_js)
assets.register('exam.js', exam_js)
assets.register('school.js', school_js)
assets.register('fullscreen.js', fullscreen_js)
assets.register('cm.js', cm_js)
assets.register('ui.css', css_ui)
