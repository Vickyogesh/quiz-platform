import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'wsgi'))

from quiz import create_app

app = create_app(extra_config='../../tests/core2/test.cfg')


def truncate_answers(engine):
    engine.execute("TRUNCATE TABLE quiz_answers;")
    engine.execute("TRUNCATE TABLE exam_answers;")
    engine.execute("TRUNCATE TABLE exams;")
    engine.execute("TRUNCATE TABLE answers;")




