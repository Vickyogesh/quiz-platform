import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'wsgi'))
from flask.ext.script import Manager
from quiz import create_app

app = create_app()

manager = Manager(app)

if __name__ == '__main__':
    manager.run()
