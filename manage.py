import sys
import os.path
sys.path.append(os.path.join(os.path.dirname(__file__), 'wsgi'))
from flask.ext.script import Manager
from flask.ext.assets import ManageAssets
from quiz import create_app
from quiz.stat import Statistics

app = create_app()

manager = Manager(app)
manager.add_command("assets", ManageAssets())
manager.add_command("stat", Statistics)


@manager.command
def list_routes():
    import urllib

    output = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(rule.methods)
        line = urllib.unquote("{:50s} {:20s} {}".format(rule.endpoint, methods, rule))
        output.append(line)

    for line in sorted(output):
        print(line)


if __name__ == '__main__':
    manager.run()
