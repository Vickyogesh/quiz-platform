.. include:: defs.hrst

Overview
========

This chapter provides high level overview of the project.

|quiz| is designed to be run in a `OpenShift <https://www.openshift.com/>`_
gear but it’s possible to setup other environments like VPS or local network.
We assume what OpenShift is used throughout the documentation.

Project Layout
--------------

This section describes the project directory structure scripts.

=========================== ====================================================
:file:`.openshift/`         OpenShift deploy scripts.
:file:`doc/`                Project documentation.
:file:`misc/`               Miscellaneous project files (config files, deploy
                            tools, initial db data etc).
:file:`tests/`              |quiz| backend tests & test tools.
:file:`web/`                |quiz| old frontends.
:file:`wsgi/`               Main sources.
:file:`wsgi/quiz/`          |quiz| WSGI module.
:file:`wsgi/.htaccess`      Apache configuration.
:program:`wsgi/application` Entry point for web server. Used by apache.
:program:`manage.py`        Project management script. For more info run
                            :samp:`python manage.py -h`.
=========================== ====================================================

|quiz| creates/uses the following OpenShift directories and files:

* :file:`$OPENSHIFT_DATA_DIR/quiz/sessions` - Session data.
* :file:`$OPENSHIFT_DATA_DIR/quiz/img` - Questions sign images.

:file:`$OPENSHIFT_DATA_DIR` also contains metrics daemon data and server side
scripts temporary files.

In a nutshell
-------------

|quiz| consist of three main parts: school pages, client pages and web API.
School pages accessible only by school account, provides information about
school and its clients statistics and allows to manage clients. Client pages
accessible by school's students (and special guest account), provides quizzes
and exams. There is also per topics and exams statistics pages. Web API provides
access to the backend features (see :doc:`api_web`).

