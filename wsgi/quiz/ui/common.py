from functools import wraps
from flask import abort, redirect, url_for, session
from flask import render_template as flask_render_template
from flask_principal import PermissionDenied
from .babel import gettext, ngettext
from ..login import QUIZ_TYPE_ID


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
        name = kwargs.get('quiz_name')

        # Interrupt on unknown quizzes.
        if name not in QUIZ_TYPE_ID:
            abort(404)
        # If user is logged in for the same quiz as requested then
        # call view function.
        elif session.get('quiz_type_name') == name:
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
    return flask_render_template(*args, **kwargs)
