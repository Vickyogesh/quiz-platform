"""
This module provides base bricks for the quiz.
"""
import re
from functools import wraps
from werkzeug.urls import Href
from flask import (
    g,
    render_template,
    current_app,
    Blueprint,
    request,
    session,
    redirect,
    url_for
)
from flask.views import View
from flask_login import current_user
from flask_principal import PermissionDenied
from .. import access

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')

# Container for registered quiz bundles.
# It will be used to get quiz_meta from outside the bundle.
# Because a bundle puts quiz_meta to g.quiz_meta on each request
# and in other places (like api blueprint) there no way to get quiz_meta.
# So this dict will be used as a workaround.
registered_quiz_meta = {}


def _camel_to_underscore(name):
    """Convert name from 'CamelCase' to 'camel_case' format.

    Used to craete endpoint from class name in the
    :meth:`BaseView.get_endpoint`.

    Based on https://gist.github.com/jaytaylor/3660565.

    Args:
        name: string in *CamelCase* format.

    Returns:
        ``name`` in *uder_score* format.
    """
    subbed = _underscorer1.sub(r'\1_\2', name)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def update_account_data():
    """Update account info from the accounts service.

    Used in the following situation:

    Client navigates to it's account page and after closing the page it
    redirect back to the original page with query parameter ``upd=1``.

    This means what quiz backend must pull new account data from the
    **Accounts Service**.

    Used in the :func:`check_access` decorator.
    """
    info = current_app.account.getUserInfo()
    account = info['user']
    session['user'] = account
    current_user.set_account(account)


def account_url(with_uid=True):
    """Returns user account page URL.
    with the fallback URL of current page.

    Example::

        http://accounts-service.com/path/to/profile?cid=...&uid=...&next...

    Args:
        with_uid: Include user ID to the query.
    """
    next_url = Href(request.url)
    url, cid = current_app.account.getUserAccountPage()
    args = {
        'cid': cid,
        'next': next_url({'upd': 1})
    }
    if with_uid is True:
        args['uid'] = current_user.account_id
    hr = Href(url)
    return hr(args)


def store_quiz_meta_in_session(meta):
    """We save metadata in session because some parts still uses info
    from session and not from quiz metadata object.

    This function gets called if client is authorized but for different quiz.
    So to not force him to login again for new quiz we just update quiz part in
    session

    See Also:
        :func:`~quiz.login.do_login` sources.

        :func:`check_access`, :class:`~quiz.common.index.IndexView`.
    """
    session['quiz_id'] = meta['id']
    session['quiz_name'] = meta['name']
    session['quiz_year'] = meta['year']
    session['quiz_fullname'] = '{0}{1}'.format(meta['name'], meta['year'])
    # Some of views uses 'back_url' in session, like ClientStatisticsView.
    session.pop('back_url', None)


#FIXME: may cause infinite recursion on access denied.
def check_access(f):
    """This decorator extends view with extra access feature.

    On access denied it redirects to login page which will redirect
    back on success login::

        site.com/login_page?next=<requested_page_url>

    Also it updates account data if ``upd=1`` query parameter is present
    in the URL.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        if current_user.is_authenticated():
            if g.quiz_meta['name'] != session.get('quiz_name'):
                store_quiz_meta_in_session(g.quiz_meta)

            # If 'upd' query parameter is set then this means account data
            # was changed and we have to sync it.
            upd = request.args.get('upd')
            if upd == '1':
                update_account_data()
            try:
                response = f(*args, **kwargs)
            except PermissionDenied:
                pass
            else:
                # If everything is ok then just return response.
                return response
        # In all other cases jump to index page which will redirect
        # to the requested page on success login.
        next_url = url_for('.%s' % f.__name__, **kwargs)
        args = {'next': next_url}
        # To prevent infinity redirection we set this mark for authorized users.
        # This mean what the user have to re authenticate to access to the
        # 'next' page. See index.IndexView class.
        if current_user.is_authenticated():
            args['reauth'] = 1
        return redirect(url_for('.index', **args))
    return wrapper


def modify_static_endpoint(app, endpoint):
    """Updates given *static* ``endpoint`` to have
    the same URL as application's *static* endpoint.

    It also makes the URL build only to  disable static files handing by
    flask on production to test (and be sure) if apache (or nginx) serve them.
    If apache/nginx configured wrongly then static files will not be
    handled at all.

    For OpenShift all static files must be placed inside ``wsgi/static``
    to be correctly handled by apache (at least for python cartridge).
    You need to add symlinks to ``wsgi/static`` if you have assets
    in other locations in ``.openshift/action_hooks/deploy``. For example::

        ln -s $OPENSHIFT_REPO_DIR/wsgi/quiz/ui/static
              $OPENSHIFT_REPO_DIR/wsgi/static/ui

    Here we create symlink for frontend's static files, now apache will serve
    urls like ``site.com/ui/static/ui/<path to asset>``.

    Args:
        app: Application instance
        endpoint: source endpoint which must have the same static URL as app's.
    """
    app_static = next(app.url_map.iter_rules('static'))
    for rule in app.url_map.iter_rules(endpoint):
        rule.rule = app_static.rule
        rule.build_only = not app.debug
        rule.refresh()


class Bundle(object):
    """Quiz bundle.

    Provides all data needed to register quiz in the flask application.

    It allows to set common quiz metadata, register pluggable views
    (:class:`BaseView`) and free functions.

    It's like a flask's :class:`Blueprint <flask.Blueprint>` but with
    some quiz related features.

    Common quiz metadata includes the following fields:

    * quiz name.
    * quiz title.
    * exam metadata (total questions, total exam time, max number of errors).
    * quiz ID in the database (see :meth:`Bundle.init_app`).
    * quiz year (see :meth:`Bundle.init_app`).

    Example metadata::

        {
            'name': 'b',
            'title': lazy_gettext('Quiz B'),
            'exam_meta': {
                'max_errors': 4,
                'total_time': 1800,
                'num_questions': 40
            }
        }

    .. note::
        Currently exams metadata must be duplicated in the
        :file:`wsgi/quiz/core/exammixin.pp` because logic is shared between
        quizzes. Later this will be fixed.
    """
    def __init__(self, import_name, meta, base_url=None):
        """Creates quiz bundle.

        Args:
            import_name: Import name for the blueprint.
            meta: Quiz metadata.
            base_url: Base URL for views.
        """
        self.import_name = import_name
        self._views = []
        self._routes = []

        #: Quiz metadata.
        #:
        #: It's a dict with common info for quiz parts, like title and
        #: quiz type ID.
        self.meta = meta

        #: URL prefix for all child views.
        #:
        #: If not set then prefix will be set as ``/<quiz name>/<quiz year>``.
        self.base_url = base_url

        self.default_rules()

    def default_rules(self):
        """Default URL rules.

        It adds logout and client fullscreen endpoints to quiz. So by default
        quiz bundle has two endpoints preconfigured:

        * logout - log out from the quiz and redirect to login page.
        * client_fullscreen - see :class:`.ClientFullscreenView`.
        """
        @self.route('/logout', methods=['GET', 'POST'])
        def logout():
            access.logout()
            return redirect(url_for('.index',
                                    _scheme='https',
                                    _external=True))

        from .client_views import ClientFullscreenView
        self.view(ClientFullscreenView)

    def modify_static_endpoint(self, app, bp_name):
        """Updates quiz blueprint's *static* endpoint to have
        the same URL as application's *static* endpoint.

        Notes:
            It used because quizzes shares a lot of web assets (js, css etc)
            so there is no reason to split static files URLs.
        """
        modify_static_endpoint(app, '%s.static' % bp_name)

    def init_app(self, app, quiz_id, quiz_year, base_prefix='',
                 no_url_year=False, year_in_title=True, main=False):
        """Register quiz in the flask application.

        Args:
            app: Falsk application.
            quiz_id: Quiz ID in the database.
            quiz_year: Quiz year.
            base_prefix: Prefix for quiz URLs.
            no_url_year: Don't put ``quiz_year`` to the attr:`Bundle.base_url`.
            main: Redirect ``/<base_prefix>`` to this quiz.

        Result URL prefix is build from :attr:`Bundle.base_url` and
        ``base_prefix``::

            /<base_prefix>/Bundle.base_url/

        """
        # Prepare result metadata as a mix of Bundle.meta and init_app()
        # parameters.
        meta = self.meta.__class__(id=quiz_id, year=quiz_year,
                                   year_in_title=year_in_title, **self.meta)
        # meta = dict(id=quiz_id, year=quiz_year, **self.meta)

        registered_quiz_meta[quiz_id] = meta

        # Create blueprint for quiz. It's name is always builds as
        # <quiz_name><quiz_year>.
        # By default static folder is set to applications one because
        # in most cases quizzes uses the same js/css and images.
        # Blueprint's templates will also be placed in the application's
        # `templates` folder (<app_root>/templates/<quiz_module_name>/).
        bp_name = '{0}{1}'.format(meta['name'], meta['year'])
        bp = Blueprint(bp_name, self.import_name, template_folder='templates',
                       static_folder='../static')

        # Quiz metadata will be placed in the Flask.g object on each request
        # and then extracted in BaseView.meta property.
        @bp.before_request
        def apply_quiz():
            g.quiz_meta = meta

        # Register bundle's pluggable views which was decorated with
        # Bundle.view().
        for view_cls in self._views:
            view_cls.register_in(bp)

        # Register bundle's free functions which was decorated with
        # Bundle.route().
        for route in self._routes:
            bp.route(route[1], **route[2])(route[0])

        # Facebook integration
        from .client_views import FacebookCanvasView
        bp.add_url_rule('/aggiungi-piattaforma-a-pagina-facebook',
                        view_func=FacebookCanvasView.get_view())

        # Create final URL prefix.
        if self.base_url is None:
            if no_url_year:
                base_url = '/{0}'.format(meta['name'])
            else:
                base_url = '/{0}/{1}'.format(meta['name'], meta['year'])
        else:
            base_url = self.base_url
        prefix = base_prefix + base_url

        # And register quiz blueprint in the application.
        app.register_blueprint(bp, url_prefix=prefix)
        self.modify_static_endpoint(app, bp_name)

        if main:
            @app.route(base_prefix + '/')
            def main_quiz():
                return redirect(url_for('%s.index' % bp_name))

    def view(self, view_cls):
        """Decorator to add pluggable views to the quiz bundle.

        Usage::

            @bundle.view
            class MyView(BaseView):
                ...
        """
        if view_cls in self._views:
            raise AssertionError('Already registered: %s' % view_cls.__name__)
        self._views.append(view_cls)
        return view_cls

    def route(self, rule, **kwargs):
        """Decorator to add view function to the quiz bundle.

        Like :meth:`flask.Flask.route` but for :class:`Bundle`.
        """
        def decorator(f):
            protect = True
            if 'check_access' in kwargs:
                protect = kwargs['check_access']
                del kwargs['check_access']
            f = check_access(f) if protect else f
            self._routes.append((f, rule, kwargs))
            return f
        return decorator


class BaseView(View):
    """Base view for all quiz views.

    It extends :class:`flask.views.View` with the following features:

    * template rendering with common values in the template context.
    * access to the quiz metadata.
    * renders a template by default.
    * redirects unauthenticated clients on login page.
    """
    #: Apply unauthenticated clients handling.
    check_access = True

    #: Template name to render.
    template_name = None

    #: Custom endpoint name. If not set then it will be built
    #: from the class name in *under_scored* format.
    #:
    #: .. seealso:: :class:`BaseView.get_endpoint`.
    endpoint = None

    #: URL rule(s).
    #:
    #: May be:
    #:
    #: None
    #:      URL will be built from class name in *under_scored* format.
    #:
    #: string
    #:      will ne used as URL.
    #:
    #: iterable with tuples (``URL``, ``**options``)
    #:      will be applied each rule. (``URL``, ``**options``) are
    #:      parameters for blueprint's route().
    #:
    #:
    #: .. seealso:: :class:`BaseView.register_in`.
    url_rule = None

    @property
    def meta(self):
        """Quiz metadata.

        See Also:
            Description in :class:`Bundle`.
        """
        return g.quiz_meta

    @property
    def quiz_fullname(self):
        """Full name of the quiz.

        Mainly used to pass to the **Accounts Service**.

        Consist of ``<quiz_name><quiz_year>``, like *b2014*.
        """
        return ''.join((self.meta['name'], str(self.meta['year'])))

    @property
    def request_lang(self):
        """Requested language.

        Returns:
            Value of ``lang`` URL query parameter if set, otherwise *it*.

        Note:
            Valid only withing request context.
        """
        return request.args.get('lang', 'it')

    def page_urls(self):
        """Returns dict with URLs for template.

        It's just a convention to use some URLs in a template. The view will
        pass ``urls`` to the template context.

        Example workflow::

            def page_urls(self):
                return {'myurl': 'http://google.com'}

        In the template.html::

            {{ urls.myurl }}

        Returns None by default (no urls will be passed to the template).
        """
        pass

    def render_template(self, **kwargs):
        """Renders :attr:`BaseView.template_name`.

        Args:
            kwargs: keyword arguments to be passed to the template.

        By default passes few parameters to the template:

        * ``quiz_meta`` - Quiz metadata.
        * ``quiz_fullname`` - ``<quiz_name><quiz_year>``.
        * ``user`` - current user object, see :class:`quiz.access.User`.
        * ``fb_appid`` - Facebook application ID.
        * ``urls`` - Page URLs, see :meth:`BaseView.page_urls`.
        """
        kwargs['quiz_meta'] = self.meta
        kwargs['quiz_fullname'] = self.quiz_fullname
        kwargs['user'] = current_user
        kwargs['fb_appid'] = current_app.config['FACEBOOK_APP_ID']

        urls = self.page_urls()
        if urls is not None:
            kwargs['urls'] = urls

        return render_template(self.template_name, **kwargs)

    def dispatch_request(self, *args, **kwargs):
        """By default renders template on request.

        Override in subclass to change this behaviour.
        """
        return self.render_template()

    @classmethod
    def get_endpoint(cls):
        """Returns final endpoint of the view class.

        It returns :attr:`BaseView.endpoint` if set otherwise constructs it
        from the class name in ``under_scored`` format without *View* postfix.

        For example::

            MySuperView -> my_super
        """
        if cls.endpoint:
            return cls.endpoint
        else:
            final_endpoint = cls.__name__
            if final_endpoint.endswith('View'):
                final_endpoint = final_endpoint[:-4]
            return _camel_to_underscore(final_endpoint)

    @classmethod
    def get_view(cls):
        """Returns view function.

        If :attr:`BaseView.check_access` is set then unauthenticated clients
        will be handled.
        """
        # Add default decorator if not present.
        # We need check_access to be called right after route so
        # we append it to the end of decorators list since they are applied
        # from the beginning of the list.
        if cls.check_access:
            if not cls.decorators:
                cls.decorators = [check_access]
            elif cls.decorators[0] != check_access:
                cls.decorators.append(check_access)
        return cls.as_view(cls.get_endpoint())

    @classmethod
    def register_in(cls, bp):
        """Register URL rules in the given blueprint."""
        view = cls.get_view()

        # Bind view class URL rules, see BaseView.url_rule docs.
        if cls.url_rule is None:
            bp.route('/%s' % cls.get_endpoint())(view)
        else:
            if isinstance(cls.url_rule, str)\
               or isinstance(cls.url_rule, unicode):
                bp.route(cls.url_rule)(view)
            else:
                for rule in cls.url_rule:
                    if len(rule) == 2:
                        bp.route(rule[0], **rule[1])(view)
                    elif len(rule) == 1:
                        bp.route(rule[0])(view)
                    else:
                        raise ValueError('Invalud URL rule')
