from flask.ext.babelex import Domain
from . import translations

domain = Domain(translations.__path__[0], domain='ui')
gettext = domain.gettext
ngettext = domain.ngettext
lazy_gettext = domain.lazy_gettext
