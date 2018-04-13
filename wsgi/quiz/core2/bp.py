from flask import Blueprint

core2 = Blueprint("core2", __name__)


@core2.route("/test")
def test():
    return "Hello"
