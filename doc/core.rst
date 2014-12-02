.. include:: defs.hrst

Core application
================

|quiz| is based on `Flask <http://flask.pocoo.org/>`_ and few
Flask extensions. Core part is implemented by
:mod:`wsgi/quiz/appcore.py <quiz.appcore>`,
:mod:`wsgi/quiz/access.py <quiz.access>` and
:mod:`wsgi/quiz/serviceproxy.py <quiz.serviceproxy>`.

:class:`~quiz.appcore.Application` extends :class:`~flask.Flask` to
provide JSON error handling, convenient configuration loading and basic
features initialization.

:class:`~quiz.appcore.Application` uses
`Flask-Login <https://flask-login.readthedocs.org/en/latest/>`_
and `Flask-Principal <https://pythonhosted.org/Flask-Principal/>`_
to manage user sessions and authentication.
Configuration of these parts is contained in :mod:`quiz.access`.

Login part uses |accounts| to get account’s info and validate credentials.
:mod:`quiz.serviceproxy`  provides :class:`~quiz.serviceproxy.AccountsApi`
class for that purpose.
This class logins to |accounts| and saves cookie data in the |quiz| session.
On next calls to |accounts| it loads cookie from the SchoolCMS session.
