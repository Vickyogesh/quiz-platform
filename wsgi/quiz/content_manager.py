from flask import Blueprint, render_template
from flask_login import current_user

cm = Blueprint('cm', __name__, static_folder='./static')


@cm.route("/")
def index():
    return render_template('content_edit.html', quiz_meta={}, user=current_user)
