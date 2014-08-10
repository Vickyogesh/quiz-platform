import re
from flask import session, request
from flask.views import View
from .util import render_template, check_access
from .. import access

_underscorer1 = re.compile(r'(.)([A-Z][a-z]+)')
_underscorer2 = re.compile('([a-z0-9])([A-Z])')


# https://gist.github.com/jaytaylor/3660565
def camel_to_underscore(name):
    subbed = _underscorer1.sub(r'\1_\2', name)
    return _underscorer2.sub(r'\1_\2', subbed).lower()


class Page(View):
    template_name = None
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
        name = camel_to_underscore(cls.__name__)
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
        return render_template(self.template_name, **kwargs)

    def on_request(self, *args, **kwargs):
        raise NotImplemented
