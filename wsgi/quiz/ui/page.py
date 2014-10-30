import re
from flask import session, request, current_app
from flask.views import View
from .util import render_template, check_access
from .. import access

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')


# https://gist.github.com/jaytaylor/3660565
def _camel_to_underscore(name):
    """Convert name from 'CamelCase' to 'camel_case' format."""
    subbed = _underscorer1.sub(r'\1_\2', name)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def register_pages(bp, page_views, ui_models):
    """Register pages with models.

    Args:
        bp: target blueprint (or app)
        page_views: dict with :class:`PageView` classes.
                    Key - page name, value - page class.
                    Page names will be linked with names from
                    :attr:`PagesMetadata.standard_page_models`.
        ui_models: list of :class:`PagesMetadata`.

    How it works
    ------------

    It dynamically creates page views with suitable models and registers
    routes for them.

    For each page in ``page_views`` will be created new :class:`PageView`
    as a subclass of the ``page_views`` class with defined
    :attr:`PageView.models`. Models will be created from ``ui_models``.

    Example::

        # Models

        class ModelX1(PageModel):
            template = 'one.html'


        class ModelX2(PageModel):
            template = 'two.html'


        class ModelY1(PageModel):
            template = 'oneY.html'


        class ModelY2(PageModel):
            template = 'twoY.html'


        # Metadata

        class MetaX(PagesMetadata):
            name = 'quiz1'
            standard_page_models = {
                'page1': ModelX1,
                'page2': ModelX2
            }


        class MetaY(PagesMetadata):
            name = 'quiz2'
            standard_page_models = {
                'page1': ModelY1,
                'page2': ModelY2
            }

        # Views

        class View1(PageView):
            rules = ({'rule': '/some/page1'})


        class View2(PageView):
            rules = ({'rule': '/some/page2'})


        page_views = {
            'page1': View1,
            'page2': View2
        }

        register_pages(bp, page_views, [MetaX, MetaY])

    As a result */some/page1* will trigger ModelX1 for quiz1 and ModelX2
    for quiz2; same for */some/page2*.
    """
    page_models = {}

    for ui in ui_models:
        if ui.standard_page_models is not None:
            for name, cls in ui.standard_page_models.iteritems():
                if name not in page_models:
                    pages = {}
                    page_models[name] = pages
                else:
                    pages = page_models[name]
                pages[ui.name] = cls
        if ui.extra_views is not None:
            for view in ui.extra_views:
                v = view.get_view()
                for rule in view.rules:
                    bp.route(**rule)(v)

    for name, cls in page_views.iteritems():
        class_name = cls.__name__
        fields = {'models': page_models.get(name)}
        view_class = type(class_name, (cls,), fields)
        v = view_class.get_view()
        for rule in view_class.rules:
            bp.route(**rule)(v)


class PageView(View):
    """Base class for pages with multiple view models.

    How it works
    ------------

    PageView has two fields to store models: :attr:`models` and
    :attr:`default_model`. Suitable model will be selected from :attr:`models`
    on each request depending on quiz name. :attr:`default_model` is used if no
    model found.

    You also may use only :attr:`default_model` if you want to share the same
    view for all quizzes.

    Page endpoint is constructed from :attr:`endpoint_prefix` and class name
    without ending *View* in underscore format.

    By default *check_access* decorator will be applied to the page;
    you also may set any decorators with :attr:`decorators`.

    Example::

        class SomeView(PageView):
            endpoint_prefix = 'fake'
            default_model = CommonModel
            models = {
                'abc': AbcModel,
                'cde': CdeModel
            }

        blueprint.route('/some/path', SomeView.get_view())

    This means what SomeView will call AbcModel instance for *abc* quizzes,
    CdeModel for *cde* quizzes and CommonModel for all other quizzes.
    View endpoint will be **fake_some**.

    On request PageView sets few useful vars and calls selected model's
    :meth:`on_request`.

    It also provides usefull :meth:`render` method which passes few values
    to the model's template. If you set :attr:`urls` then it may be used
    in template like::

        {{ urls|tojson }}

    The following attributes will be set before calling
    :meth:`PageModel.on_request`:
    * quiz_id - quiz ID.
    * quiz_name - quiz base name part.
    * quiz_year - quiz year part.
    * quiz_fullname - quiz fullname.
    * uid - user ID.
    * lang - request language.

    The following values will be passed to template by default if you
    call :meth:`PageView.render`::
    * quiz_name
    * quiz_year
    * quiz_fullname
    * lang
    * user
    * urls - *if not None*
    """
    #: Default model class
    default_model = None

    #: A dict with page models.
    #: Key - quiz name, value - model class.
    models = {}

    #: Prefix string for the view's endpoint.
    #: Result endpoint format: [<endpoint_prefix>_]<class_name>
    endpoint_prefix = None

    #: Iterable of dicts which represents kwargs for the
    #: :meth:`flask.Blueprint.route`.
    #: Used by :func:`register_pages`.
    rules = None

    def __init__(self):
        super(PageView, self).__init__()
        self.model = None
        self.template = None
        self.quiz_id = None
        self.quiz_name = None
        self.quiz_year = None
        self.quiz_fullname = None
        self.lang = None
        self.uid = None
        self.urls = None
        self._setup_models()

    @classmethod
    def get_view(cls, custom_endpoint=None):
        """Create view function of the class.

        If ``custom_endpoint`` is not set then endpoint will be
        generated from the class name and :attr:`endpoint_prefix`.
        """
        if custom_endpoint is None:
            # Convert class name to under_score format.
            # Exclude 'View' from the end if present.
            name = cls.__name__
            if name.endswith('View'):
                name = name[:-4]
            name = _camel_to_underscore(name)

            # View endpoint: <prefix>_<class_name>
            if cls.endpoint_prefix is None:
                ep = name
            else:
                ep = '%s_%s' % (cls.endpoint_prefix, name)
        else:
            ep = custom_endpoint

        # Add default decorator if not present.
        # We need check_access to be called right after route so
        # we append it to the end of decorators list since they are applied
        # from the beginning of the list.
        if cls.decorators is None:
            cls.decorators = [check_access]
        elif cls.decorators[0] != check_access:
            cls.decorators.append(check_access)

        return cls.as_view(ep)

    # Create models instances.
    def _setup_models(self):
        self._model_list = {}
        if self.default_model is not None:
            self._default_model = self.default_model(self)

        if self.models is not None:
            for name, cls in self.models.iteritems():
                self._model_list[name] = cls(self)

    def dispatch_request(self, *args, **kwargs):
        self.quiz_id = session['quiz_id']
        self.quiz_name = session['quiz_name']
        self.quiz_year = session['quiz_year']
        self.quiz_fullname = session['quiz_fullname']
        self.uid = access.current_user.account_id
        self.lang = request.args.get('lang', 'it')
        self.urls = None
        self.model = self._model_list.get(self.quiz_name, self._default_model)
        self.template = self.model.template
        return self.model.on_request(*args, **kwargs)

    def render(self, **kwargs):
        kwargs['quiz_name'] = self.quiz_name
        kwargs['quiz_year'] = self.quiz_year
        kwargs['quiz_fullname'] = self.quiz_fullname
        kwargs['lang'] = self.lang
        kwargs['user'] = access.current_user
        kwargs['fb_appid'] = current_app.config['FACEBOOK_APP_ID']
        if self.urls is not None:
            kwargs['urls'] = self.urls
        self.model.update_render_context(kwargs)
        return render_template(self.template, **kwargs)


class PageModel(object):
    """Base class for the :class:`PageView` models.

    In subclass you may override :meth:`on_request`;
    by default it just renders template.
    :attr:`self.page` provides parent page.

    Page models is used to provide different views of the page depending
    on quiz. You may have multiple page representations for the same endpoint
    but for different quizzes. See :class:`PageView` for more info.
    """
    #: Template name for the model.
    template = None

    def __init__(self, page):
        self.page = page

    def update_render_context(self, ctx):
        pass

    def on_request(self, *args, **kwargs):
        """This method is called on each request with all the arguments
        from the URL rule.
        """
        return self.page.render(**kwargs)


# TODO: class name is unclear.
class PagesMetadata(object):
    """Helper class which provides models for the specific quiz type.

    It used by :func:`register_pages` to create urls and views.
    """
    #: Quiz name for which models are provided.
    name = None

    #: dict with pages' models classes.
    #: Key - page name, value - model class.
    #: Example::
    #:
    #:  {'page1': SomeModel, 'page2': PageModel}
    #:
    #: Models will be linked with views with the same names.
    #: See :func:`register_pages` for more info.
    standard_page_models = None

    #: List of extra views to register (PageView).
    extra_views = None
