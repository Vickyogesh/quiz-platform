from functools import wraps
from werkzeug.urls import Href
from flask import abort, redirect, url_for, session, request
from flask import render_template as flask_render_template
from flask_principal import PermissionDenied
from .babel import gettext, ngettext, lazy_gettext
from .. import app
from ..access import current_user
from ..login import QUIZ_ID_MAP

QUIZ_TITLE = {
    1: lazy_gettext('Quiz Patente 2011'),
    2: lazy_gettext('CQC'),
    3: lazy_gettext('Quiz Patente 2013'),
    4: lazy_gettext('Scooter'),
    # Truck
    5: lazy_gettext('Truck C1 and C1E'),
    6: lazy_gettext('Truck C1 and C1E non-professional'),
    7: lazy_gettext('Truck C and CE'),
    8: lazy_gettext('Truck C and CE with C1 and C1E category'),
    9: lazy_gettext('Truck D1 and D1E'),
    10: lazy_gettext('Truck D and DE'),
    11: lazy_gettext('Truck D and DE with D1 and D1E category')
}


#FIXME: may cause infinite recursion on access denied.
def check_access(f):
    """This decorator extends view with extra access features:

        * On access denied it redirects to login page which will redirect
          back on success login.

        * If quiz name is invalid then HTTP 404 will be returned.

        * If quiz name conflicts with current user's one then
          it will be redirected to login page.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        name = session.get('quiz_fullname')

        # Interrupt on unknown quizzes.
        if name is not None and name not in QUIZ_ID_MAP:
            abort(404)
        else:
            # If 'upd' query parameter is set then this means account data
            # was changed and we have to sync it.
            upd = request.args.get('upd')
            if upd == '1':
                update_account_data()
            try:
                response = f(*args, **kwargs)
            except PermissionDenied:
                pass
            # If everything is ok then just return response.
            else:
                return response

        # In all other cases jump to index page which will redirect
        # to the requested page on success login.
        next_url = url_for('.%s' % f.__name__, **kwargs)
        return redirect(url_for('.index', quiz_name=name, next=next_url))
    return wrapper


def render_template(*args, **kwargs):
    """Adds to the flask's render_template domain's translation functions."""
    kwargs['_'] = gettext
    kwargs['_gettext'] = gettext
    kwargs['_ngettext'] = ngettext
    quiz_title = QUIZ_TITLE.get(session.get('quiz_id'))
    if quiz_title is not None:
        kwargs['quiz_title'] = quiz_title
    return flask_render_template(*args, **kwargs)


def account_url(with_uid=True):
    """Accounts URL with the fallback URL of current page."""
    next_url = Href(request.url)
    url, cid = app.account.getUserAccountPage()
    args = {
        'cid': cid,
        'next': next_url({'upd': 1})
    }
    if with_uid is True:
        args['uid'] = current_user.account_id
    hr = Href(url)
    return hr(args)


def update_account_data():
    """Update account info from the accounts service."""
    info = app.account.getUserInfo()
    account = info['user']
    session['user'] = account
    current_user.set_account(account)
