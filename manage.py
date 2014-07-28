import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'wsgi'))
from flask.ext.script import Manager
from flask.ext.assets import ManageAssets
from quiz import create_app

app = create_app()

manager = Manager(app)
manager.add_command("assets", ManageAssets())

if __name__ == '__main__':
    manager.run()
