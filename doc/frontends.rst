.. include:: defs.hrst

Frontends
=========

Each quiz type in the |quiz| has its own frontend which is fully independent of
other quizzes. There is a helper package - :mod:`quiz.common` -
that aims to build frontends since most of the features are common
in all quizzes.

Core part is implemented in the :mod:`quiz.common.base`. It represents each
frontend as :ref:`flask's blueprint <flask:blueprints>`. Endpoints are
supposed to the represented by :ref:`Pluggable Views <flask:views>` but not
restricted to.

:class:`~quiz.common.base.BaseView` represents one endpoint as
:ref:`pluggable view <flask:views>` and it's main purpose is provide quiz
metadata for the request handler. It also renders template with some useful
context values and automates endpoint creation. All features are described in
the :class:`API docs <quiz.common.base.BaseView>`.

:class:`~quiz.common.base.Bundle` represents whole quiz. All endpoints must be
registered in it. You may think of it as a :ref:`blueprint <flask:blueprints>`
but more quiz specific. Additionally to the registered endpoints it adds few
common ones for logout ans static files. One of the feature is a possibility
to register multiple frontends for the same quiz type but with different
parameters. For example, you may register quiz CQC for 2011 and 2014 years which
will use different set of questions and account permissions but
one quiz bundle. See :class:`API docs <quiz.common.base.Bundle>` for more info.

Common views are implemented by :mod:`quiz.common.client_views` - for clients,
:mod:`quiz.common.school_views` - for schools, and
:mod:`quiz.common.index` - for login page.
Some of them are supposed to be subclassed and some of them may be used as is.

Typical forntend building workflow is to combine few already implemented views
and custom quiz specific ones in a bundle. Also html templates maybe extended.
