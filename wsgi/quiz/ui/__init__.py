from flask import Blueprint

ui = Blueprint('ui', __name__,
               template_folder='templates', static_folder='static',
               static_url_path='/static/ui')

from . import babel
from . import index
from . import menu
from . import statistics
