from flask import Blueprint, abort, Response, url_for
from ..login import QUIZ_ID_MAP

#NOTE: g.line.js has some changes/fixes.
ui = Blueprint('ui', __name__,
               template_folder='templates', static_folder='static',
               static_url_path='/static/ui')

from . import babel
from . import index
from . import school
from . import client
from . import util
from . import fullscreen

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
