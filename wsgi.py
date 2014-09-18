#!/usr/bin/python
import os
import sys

virtenv = os.environ['OPENSHIFT_PYTHON_DIR'] + '/virtenv/'
virtualenv = os.path.join(virtenv, 'bin/activate_this.py')
try:
    execfile(virtualenv, dict(__file__=virtualenv))
except IOError:
    pass

print "Runs wsgi.py"

sys.path.append(os.path.join(os.path.dirname(__file__), 'wsgi'))
from quiz import create_app
application = create_app()
