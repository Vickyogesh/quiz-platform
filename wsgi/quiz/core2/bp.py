from flask import Blueprint

core2 = Blueprint("core2", __name__)

from .quiz import *
from .exam import *
