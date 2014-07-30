import hashlib
from werkzeug.exceptions import HTTPException
from flask import redirect, url_for, flash, request, session, abort
from flask_wtf import Form
from flask_login import current_user
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired
from . import ui
from .babel import lazy_gettext, gettext
from .common import render_template
from .. import app, access
from ..login import QUIZ_TYPE_ID, do_login


def after_login():
    """Redirect to menu page or to the page specified in the URL query
    parameter 'next'.
    """
    next_url = request.args.get('next')
    if next_url is not None:
        return redirect(next_url)
    else:
        return redirect(url_for('.menu'))


class LoginFrom(Form):
    name = StringField(lazy_gettext('Login'), validators=[DataRequired()])
    pwd = PasswordField(lazy_gettext('Password'), validators=[DataRequired()])


@ui.route('/', defaults={'quiz_name': 'b2013'}, methods=['GET', 'POST'])
@ui.route('/<word:quiz_name>', methods=['GET', 'POST'])
def index(quiz_name):
    if quiz_name not in QUIZ_TYPE_ID:
        abort(404)

    # Skip login for already signed users (for the given quiz).
    if current_user.is_authenticated() and (current_user.is_school
                                            or current_user.is_school_member):
        if session['quiz_type_name'] == quiz_name:
            return after_login()

    form = LoginFrom()
    if form.validate_on_submit():
        login = form.name.data
        passwd = form.pwd.data
        nonce = app.account.get_auth().get('nonce', '')
        digest = hashlib.md5('{0}:{1}'.format(login, passwd)).hexdigest()
        digest = hashlib.md5('{0}:{1}'.format(nonce, digest)).hexdigest()
        try:
            do_login({
                'nonce': nonce,
                'login': login,
                'appid': '32bfe1c505d4a2a042bafd53993f10ece3ccddca',
                'quiz_type': quiz_name,
                'digest': digest
            })
        except HTTPException as e:
            if e.code == 403:
                flash(gettext('Forbidden.'))
            else:
                flash(e.description)
        else:
            return after_login()
    return render_template('ui/index.html', quiz_name=quiz_name, form=form)


@ui.route('/logout')
@access.login_required
def logout():
    quiz_name = session['quiz_type_name']
    access.logout()
    return redirect(url_for('.index', quiz_name=quiz_name))
