import re
from flask import session, request
from flask.views import View
from .util import render_template, check_access
from .. import access

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')


# https://gist.github.com/jaytaylor/3660565
def _camel_to_underscore(name):
    subbed = _underscorer1.sub(r'\1_\2', name)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


def register_pages(bp, page_views, ui_models):
    page_models = {}

    for ui in ui_models:
        for name, cls in ui.standard_page_models.iteritems():
            if name not in page_models:
                pages = {}
                page_models[name] = pages
            else:
                pages = page_models[name]
            pages[ui.name] = cls

    for name, cls in page_views.iteritems():
        class_name = cls.__name__[:-4]  # name without 'View'
        fields = {'models': page_models.get(name)}
        view_class = type(class_name, (cls,), fields)
        v = view_class.get_view()
        for rule in view_class.rules:
            bp.route(**rule)(v)


class PageModels(object):
    name = None
    standard_page_models = None


class PageView(View):
    models = {}
    endpoint_prefix = None
    default_model = None

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
    def get_view(cls):
        name = _camel_to_underscore(cls.__name__)
        ep = '%s_%s' % (cls.endpoint_prefix, name)

        # Add default decorator if not present.
        # We need check_access to be called right after route so
        # we append it to the end of decorators list since they are applied
        # from the beginning of the list.
        if cls.decorators is None:
            cls.decorators = [check_access]
        elif cls.decorators[0] != check_access:
            cls.decorators.append(check_access)

        return cls.as_view(ep)

    def _setup_models(self):
        self._model_list = {}
        if self.default_model is not None:
            self.default_model = self.default_model(self)

        if self.models is not None:
            for name, cls in self.models.iteritems():
                if name == '' and self.default_model is None:
                    self.default_model = cls(self)
                else:
                    self._model_list[name] = cls(self)

    def dispatch_request(self, *args, **kwargs):
        self.quiz_id = session['quiz_id']
        self.quiz_name = session['quiz_name']
        self.quiz_year = session['quiz_year']
        self.quiz_fullname = session['quiz_fullname']
        self.uid = access.current_user.account_id
        self.lang = request.args.get('lang', 'it')
        self.urls = None
        self.model = self._model_list.get(self.quiz_name, self.default_model)
        self.template = self.model.template
        return self.model.on_request(*args, **kwargs)

    def render(self, **kwargs):
        kwargs['quiz_name'] = self.quiz_name
        kwargs['quiz_year'] = self.quiz_year
        kwargs['quiz_fullname'] = self.quiz_fullname
        kwargs['lang'] = self.lang
        kwargs['user'] = access.current_user
        if self.urls is not None:
            kwargs['urls'] = self.urls
        return render_template(self.template, **kwargs)


class PageModel(object):
    template = None

    def __init__(self, page):
        self.page = page

    def on_request(self, *args, **kwargs):
        return self.page.render(**kwargs)


class ClientPage(PageView):
    decorators = [access.be_client_or_guest.require()]
    endpoint_prefix = 'client'


class Page(View):
    # This template will be used if no template will be found in
    # 'templates'.
    default_template = None

    # Specific templates for quizzes. Key is quiz name, value - template.
    templates = {}

    # Result page endpoint is <endpoint_prefix>_<class_name>.
    # See get_view().
    endpoint_prefix = None

    def __init__(self):
        super(Page, self).__init__()
        self.quiz_type = None
        self.quiz_name = None
        self.lang = None
        self.uid = None
        self.urls = None

    @classmethod
    def get_view(cls):
        name = _camel_to_underscore(cls.__name__)
        ep = '%s_%s' % (cls.endpoint_prefix, name)

        # Add default decorator if not present.
        # We need check_access to be called right after route so
        # we append it to the end of decorators list since they are applied
        # from the beginning of the list.
        if cls.decorators is None:
            cls.decorators = [check_access]
        elif cls.decorators[0] != check_access:
            cls.decorators.append(check_access)

        return cls.as_view(ep)

    def get_template_name(self):
        """Return template path depending on quiz name.

        At first this function searches template in 'templates' and then,
        if nothing found, returns 'default_template'.
        """
        return self.templates.get(self.quiz_name, self.default_template)

    def get_quiz_template_params(self):
        """Returns a dict with quiz specific parameters for the template.
        """
        func = getattr(self, '%s_template_params' % self.quiz_name, None)
        if func is not None:
            return func()

    def dispatch_request(self, *args, **kwargs):
        self.quiz_type = session['quiz_type']
        self.quiz_name = session['quiz_type_name']
        self.lang = request.args.get('lang', 'it')
        self.uid = access.current_user.account_id
        self.urls = None
        return self.on_request(*args, **kwargs)

    def render(self, **kwargs):
        kwargs['quiz_type'] = self.quiz_type
        kwargs['quiz_name'] = self.quiz_name
        kwargs['lang'] = self.lang
        kwargs['user'] = access.current_user
        if self.urls is not None:
            kwargs['urls'] = self.urls
        extra = self.get_quiz_template_params()
        if extra is not None:
            kwargs.update(extra)
        return render_template(self.get_template_name(), **kwargs)

    def on_request(self, *args, **kwargs):
        raise NotImplemented
