"""
This module provides user session and authentication features.
"""
from functools import partial
from werkzeug.utils import cached_property
from itsdangerous import URLSafeTimedSerializer
from flask import session, current_app
from flask_login import (
    LoginManager,
    UserMixin,
    current_user,
    login_user,
    logout_user,
    login_required
)
from flask_principal import (
    Principal,
    Need,
    RoleNeed,
    UserNeed,
    Permission,
    Identity,
    AnonymousIdentity,
    identity_loaded,
    identity_changed
)

from . import app

# http://thecircuitnerd.com/flask-login-tokens/
# Login_serializer used to encrypt and decrypt the cookie token for the remember
# me option of flask-login
login_serializer = URLSafeTimedSerializer(app.secret_key)

login_manager = LoginManager()

# To support sphinx autodoc extension we check for app
# since it will not be created on autodoc's import action.
if app:
    login_manager.init_app(app)
    Principal(app)


###########################################################
### Permissions
###########################################################

ParentSchoolNeed = partial(Need, 'school_id')
be_admin = Permission(RoleNeed('admin'))
be_content_manager = Permission(RoleNeed('content_manager'))
be_school = Permission(RoleNeed('school'))
be_client = Permission(RoleNeed('student'))
be_admin_or_school = Permission(RoleNeed('admin'), RoleNeed('school'))
be_client_or_guest = Permission(RoleNeed('student'), RoleNeed('guest'))
be_user = Permission(RoleNeed('student'), RoleNeed('admin'), RoleNeed('school'),
                     RoleNeed('guest'))


class OwnerPermission(Permission):
    def __init__(self, id):
        need = UserNeed(id)
        super(OwnerPermission, self).__init__(need)


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user

    if not hasattr(current_user, 'account'):
        return

    identity.provides.add(UserNeed(current_user.account['id']))
    identity.provides.add(RoleNeed(current_user.user_type))

    if current_user.is_student:
        school_id = current_user.account['school_id']
        identity.provides.add(ParentSchoolNeed(school_id))


###########################################################
### Login
###########################################################

class User(UserMixin):
    """User class represents an account and aims to provide
    information for the login manager about it.
    """
    def __init__(self, account):
        self.account = account

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return self.account['login']

    def get_auth_token(self):
        data = [self.account['login'], self.account.get('passwd')]
        return login_serializer.dumps(data)

    def set_account(self, account):
        self.__dict__.clear()
        self.account = account

    @cached_property
    def account_id(self):
        return self.account['id']

    @cached_property
    def user_type(self):
        return self.account['type']

    @cached_property
    def is_admin(self):
        return self.user_type == 'admin'

    @cached_property
    def is_content_manager(self):
        return self.user_type == 'content_manager'

    @cached_property
    def is_readonly(self):
        return self.account.get('readonly', False)

    @cached_property
    def is_school(self):
        return self.user_type == 'school'

    @cached_property
    def is_student(self):
        return self.user_type == 'student'

    @cached_property
    def is_guest(self):
        return self.user_type == 'guest'

    @cached_property
    def is_school_member(self):
        return self.is_guest or self.is_student


# Load user from session.
@login_manager.user_loader
def load_user(uid):
    try:
        account = session['user']
        if account['id'] != uid and account['login'] != uid:
            return None
    except KeyError:
        return None
    return User(account)

def login(account, remember=False):
    """Create user object for the `account`, save it in the session and
    call LoginManager's login routine.
    """
    session['user'] = account
    user = User(account)
    login_user(user, remember=remember)
    identity_changed.send(current_app._get_current_object(),
                          identity=Identity(user.get_id()))


def logout():
    """Clean session from the user object and call
    LoginManager's logout routine.

    It also logout from **Accounts Service**.
    """
    app.account.logout()
    session.delete()
    logout_user()
    # Tell Flask-Principal the user is anonymous
    identity_changed.send(current_app._get_current_object(),
                          identity=AnonymousIdentity())
