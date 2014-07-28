from flask import Blueprint
from flask.ext.assets import Bundle
from .. import assets

ui = Blueprint('ui', __name__,
               template_folder='templates', static_folder='static',
               static_url_path='/static/ui')

# Other filters 'yui_js', 'rjsmin'.
js_base = Bundle('ui/js/libs/raphael-min.js', 'ui/js/libs/g.raphael-min.js',
                 'ui/js/libs/g.line.js', 'ui/js/libs/g.pie.js',
                 filters='jsmin', output='ui/gen/base_libs.js')

js_bb = Bundle('ui/js/libs/json2.js', 'ui/js/libs/underscore-min.js',
               'ui/js/libs/backbone-min.js',
               filters='jsmin', output='ui/gen/bb.js')

js_ui = Bundle('ui/js/chart.js', 'ui/js/expressbar.js', 'ui/js/userstat.js',
               filters='jsmin', output='ui/gen/ui.js')

css_ui = Bundle('ui/css/style.css', 'ui/css/startup.css',
                'ui/css/menu.css', 'ui/css/statistics.css',
                filters='cssmin', output='ui/gen/ui.css')

assets.register('base_libs.js', js_base)
assets.register('bb.js', js_bb)
assets.register('ui.js', js_ui)
assets.register('ui.css', css_ui)

from . import babel
from . import index
from . import menu
from . import statistics
