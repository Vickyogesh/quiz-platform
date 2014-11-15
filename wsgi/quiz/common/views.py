from flask import redirect, url_for, request
from .base import BaseView, account_url
from .. import access


class ClientView(BaseView):
    """Base client page view.

    It adds to the :class:`BaseView` client permission check and account URL
    for template.
    """
    decorators = [access.be_client_or_guest.require()]

    @staticmethod
    def account_url():
        return account_url()

    def page_urls(self):
        return {'account': ClientView.account_url()}


class ClientFullscreenView(ClientView):
    """Common page with fullscreen wrapper for all client's pages.
    It fallbacks to normal pages for mobile browsers.
    """
    template_name = 'client_fullscreen_wrapper.html'
    url_rule = '/fmenu'
    endpoint = 'client_fullscreen'

    @classmethod
    def is_mobile(cls):
        p = request.user_agent.platform

        if p == 'android' or p == 'iphone' or p == 'ipad' or \
           (p == 'windows' and 'Phone' in request.user_agent.string):
            return True
        return False

    def dispatch_request(self, *args, **kwargs):
        if ClientFullscreenView.is_mobile():
            return redirect(url_for('.client_menu'))
        else:
            return self.render_template()
