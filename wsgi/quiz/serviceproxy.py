try:
    import simplejson as json
except ImportError:
    import json

import requests
import hashlib
from flask import current_app
from urlparse import urlparse
from werkzeug.http import dump_cookie, parse_dict_header
from werkzeug.exceptions import default_exceptions, abort


############################################################
# Base class.
############################################################

class HttpServiceProxy(object):
    """This class allows to send HTTP requests and save session data
    inside another session object.
    """

    # Key in the session of the caller service
    # to store target service session data.
    STORAGE_KEY = 'proxyservice.session'

    def __init__(self, target_url, target_cookie_name,
                 target_cookie_domain=None, session_func={}, call_save=True):
        """Construct ServiceProxy object.

        Args:
            target_url: URL of the target service.
                        It will be used by default for all requests.
            target_cookie_name: Session cookie name of the target service.
            target_cookie_domain: Session cookie domain of the target service.
            session_func: Function which returns current session object.
                          It used to save data of target service session
                          If you authorize only with one user then leave
                          it default.
            call_save: Call session_object.save() to save session changes
                       (if save method is provided).

        session_func may be a dic or function like:

            def func():
                reutrn session_object

        ServiceProxy also provides root_url which is a base URL
        of the target_url.
        """
        # Setup URLs
        def without_trailing_slash(url):
            return url[:-1] if url[-1] == '/' else url
        self.default_url = without_trailing_slash(target_url)
        self.root_url = self.__get_root_url(self.default_url)
        self.root_url = without_trailing_slash(self.root_url)

        # Target service session cookie name.
        self.target_cookie_name = target_cookie_name
        self.target_cookie_domain = target_cookie_domain

        # If session_func is a dict then we wont call save().
        # If session_func is a function then check call_save param.
        self.session_func = session_func
        if isinstance(session_func, dict):
            self.__is_dict = True
            self.__call_save = False
        else:
            self.__is_dict = False
            self.__call_save = call_save or hasattr(self._session, 'save')

    # Return root part of the url.
    def __get_root_url(self, url):
        r = urlparse(url)
        return '%s://%s' % (r.scheme, r.netloc) if r.scheme else r.netloc

    def __add_header(self, dest, key, val):
        if 'headers' in dest:
            headers = dest['headers']
            headers[key] = val
        else:
            dest['headers'] = {key: val}

    # Return session object.
    @property
    def _session(self):
        return self.session_func if self.__is_dict else self.session_func()

    # Return target service session cookie.
    @property
    def _session_cookie(self):
        return self._session[self.STORAGE_KEY]

    # Construct accounts service URL.
    def _url(self, path, use_root):
        return (self.root_url if use_root else self.default_url) + path

    # Save target service cookie in the current session for later use.
    def _save_session(self, response):
        if self.target_cookie_name in response.cookies:
            c = dump_cookie(self.target_cookie_name,
                            response.cookies[self.target_cookie_name],
                            domain=self.target_cookie_domain)
            self._session[self.STORAGE_KEY] = c
            if self.__call_save:
                self._session.save()

    # Apply saved session for the target request.
    # TODO: what if we already have 'Cookie' - currently it will be replaced.
    def _apply_session(self, dest):
        if self.STORAGE_KEY in self._session:
            if self._session_cookie is None:
                return
            self.__add_header(dest, 'Cookie', self._session_cookie)

    # Return use_root value if present, otherwise return False
    # (also remove it from the dict).
    def __use_root(self, kwargs):
        use_root = kwargs.get('use_root', False)
        if 'use_root' in kwargs:
            del kwargs['use_root']
        return use_root

    def get(self, path, **kwargs):
        """Send a GET request to the target service.

        Args:
            path: Target service relative path (/<path>).
                  If 'use_root' is present in the kwargs and equals to True
                  then root_url will be used as base URL, otherwise
                  default_url will be used.
            kwargs: requests lib parameters (except 'use_root').

        Returns: response object.
        """
        self._apply_session(kwargs)
        use_root = self.__use_root(kwargs)
        r = requests.get(self._url(path, use_root), **kwargs)
        self._save_session(r)
        return r

    def post(self, path, **kwargs):
        """Send a POST request to the target service.

        Args:
            path: Target service relative path (/<path>).
                  If 'use_root' is present in the kwargs and equals to True
                  then root_url will be used as base URL, otherwise
                  default_url will be used.
            kwargs: requests lib parameters (except 'use_root').

        Returns: response object.
        """
        self._apply_session(kwargs)
        use_root = self.__use_root(kwargs)
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, dict):
                kwargs['data'] = json.dumps(data)
            if 'content-type' not in kwargs:
                self.__add_header(kwargs, 'content-type', 'application/json')
        r = requests.post(self._url(path, use_root), **kwargs)
        self._save_session(r)
        return r

    def put(self, path, **kwargs):
        """Send a PUT request to the target service.

        Args:
            path: Target service relative path (/<path>).
                  If 'use_root' is present in the kwargs and equals to True
                  then root_url will be used as base URL, otherwise
                  default_url will be used.
            kwargs: requests lib parameters (except 'use_root').

        Returns: response object.
        """
        self._apply_session(kwargs)
        use_root = self.__use_root(kwargs)
        r = requests.put(self._url(path, use_root), **kwargs)
        self._save_session(r)
        return r

    def delete(self, path, **kwargs):
        """Send a DELETE request to the target service.

        Args:
            path: Target service relative path (/<path>).
                  If 'use_root' is present in the kwargs and equals to True
                  then root_url will be used as base URL, otherwise
                  default_url will be used.
            kwargs: requests lib parameters (except 'use_root').

        Returns: response object.
        """
        self._apply_session(kwargs)
        use_root = self.__use_root(kwargs)
        r = requests.delete(self._url(path, use_root), **kwargs)
        self._save_session(r)
        return r


############################################################
# Services proxies.
############################################################

def _check_json_response_status(response):
    """This function raises an error if the `response` status is not 200 OK.

    If `response` contains json error with description then it will be
    appended to the error.
    """
    if response.status_code != 200:
        code = response.status_code
        try:
            data = response.json()
        except:
            data = None

        if (data is None or 'description' not in data
           or code not in default_exceptions):
            abort(code)
        else:
            raise default_exceptions[code](description=data['description'])


def _create_digest(salt_or_nonce, passwd):
    m = hashlib.md5()
    m.update('{}:{}'.format(salt_or_nonce, passwd))
    return m.hexdigest()

def salt():
    s = current_app.config['SALT']
    if not s:
        raise Exception('Failed to get salt')
    return s

class AccountsApi(HttpServiceProxy):
    """This class provides Accounts service API."""
    def __init__(self, target_url, target_cookie_name='tw_acc_session',
                 target_cookie_domain=None, session_func={}, call_save=True):
        super(AccountsApi, self).__init__(target_url, target_cookie_name,
                                          target_cookie_domain,
                                          session_func, call_save)

    def get_auth(self):
        """Get auth information from the Account Service.

        Returns: a dict with auth data (currently contains only 'nonce')
        """
        response = self.get('/login')
        hdr = response.headers['WWW-Authenticate']
        hdr = parse_dict_header(hdr[6:])
        return hdr

    def send_auth(self, login, passwd_digest, passwd_digest_old, nonce, caller_service):
        """Send auth info to the Accounts Service.

        Args: accounts service auth args.

        Returns: tuple with account info and session cookie.

        Raises: werkzeug's exception respective to status code.
        """
        hdr = 'QAuth nonce="{0}", username="{1}", response="{2}", response_old="{3}"'
        hdr = hdr.format(nonce, login, passwd_digest, passwd_digest_old or '')
        hdr = {'Authenticate': hdr}

        if caller_service is not None:
            hdr['X-Account-Service'] = caller_service

        response = self.post('/login', headers=hdr)
        _check_json_response_status(response)
        data = response.json()
        del data['status']
        return data, self._session_cookie

    def send_fb_auth(self, id, token, caller_service, app_id=None, secret=None):
        """Send auth info to the Accounts Service.

        Args: accounts service auth args.

        Returns: tuple with account info and session cookie.

        Raises: werkzeug's exception respective to status code.
        """
        hdr = 'QAuth fbid="{0}", fbtoken="{1}"'
        hdr = hdr.format(id, token)

        if app_id is not None and secret is not None:
            hdr += ', appid="%s", secret="%s"' % (app_id, secret)

        hdr = {'Authenticate': hdr}

        if caller_service is not None:
            hdr['X-Account-Service'] = caller_service

        response = self.post('/login', headers=hdr)
        _check_json_response_status(response)
        data = response.json()
        del data['status']
        return data, self._session_cookie

    def login(self, login, passwd, caller_service):
        """Login to the Accounts Service."""
        info = self.get_auth()
        passwd_digest = _create_digest(salt(), passwd)
        passwd_digest = _create_digest(info['nonce'], passwd_digest)

        account = self.send_auth(login, passwd_digest, info['nonce'],
                                 caller_service)
        return account

    def logout(self):
        """Logout from the Accounts Service."""
        response = self.post('/logout')
        _check_json_response_status(response)

    def getSchools(self):
        """Get schools list."""
        response = self.get('/schools')
        _check_json_response_status(response)
        return response.json()

    def getSchoolConfig(self, s_id):
        response = self.get('/school_config/{}'.format(s_id))
        try:
            response = response.json()
            return json.loads(response['data'])
        except:
            return None

    # name, login, passwd, access=None
    def addSchool(self, **kwargs):
        """Register new school.

        Args: The following parameters are expected:

              ======    =====================================
              name      School name.
              login     School login.
              passwd    School password.
              access    School access permissions (optional).
              ======    =====================================

        You may provide string parameter 'raw' instead of key-values.
        It must be well formed JSON string with above fields.
        """
        if 'raw' in kwargs:
            raw = kwargs['raw']
            if 'access: ' not in raw and raw != '{}':
                kwargs = raw[:-1] + ', "access": {"b2011": "2150-01-01"}}'
        else:
            if 'access' not in kwargs:
                kwargs['access'] = {'b2011': '2150-01-01'}

        response = self.post('/schools', data=kwargs)
        _check_json_response_status(response)
        return response.json()

    def removeSchool(self, school_id):
        """Remove registered school."""
        response = self.delete('/schools/{0}'.format(school_id))
        _check_json_response_status(response)
        return response.json()

    # Not tested.
    def updateSchool(self, school_id, **kwargs):
        """Update school's accout information.

        Args:
            school_id: School ID.
            kwargs: The following parameters are allowed:

                    ================    ========================
                    name                School name.
                    passwd              School password.
                    access_quiz_b       Access to QuizB.
                    access_quiz_boat    Access to QuizBoat.
                    access_quiz_bike    Access to QuizBike.
                    access_ebook        Access to ebook service.
                    ================    ========================

        You may provide string parameter 'raw' instead of key-values.
        It must be well formed JSON string with above fields.
        """
        if 'raw' in kwargs:
            kwargs = kwargs['raw']
        response = self.put('/schools/{0}'.format(school_id), data=kwargs)
        _check_json_response_status(response)
        return response.json()

    def getSchoolStudents(self, school_id, id_list=None):
        if id_list is None:
            url = '/schools/{0}/students'.format(school_id)
        else:
            ids = ','.join(str(x) for x in id_list)
            url = '/schools/{0}/students?id={1}'.format(school_id, ids)
        response = self.get(url)
        _check_json_response_status(response)
        return response.json()

    # name, surname, login, passwd
    def addStudent(self, school_id, **kwargs):
        """Add a student to the given school.

        Args:
            school_id: Parent school ID.
            kwargs: The following parameters are expected:

                    ======= ================
                    name    Student name.
                    surname Student surname.
                    email   Student email. (optional)
                    login   Student login.
                    passwd  Student passwd.
                    ======= ================

        You may provide string parameter 'raw' instead of key-values.
        It must be well formed JSON string with above fields.
        """
        if 'raw' in kwargs:
            kwargs = json.loads(kwargs['raw'])
            kwargs['passwd'] = _create_digest(salt(), kwargs['passwd'])
        response = self.post('/schools/{0}/students'.format(school_id),
                             data=json.dumps(kwargs))
        _check_json_response_status(response)
        return response.json()

    def getStudent(self, id):
        """Get account information for the given student."""
        response = self.get('/students/{0}'.format(id))
        _check_json_response_status(response)
        return response.json()

    def removeStudent(self, id):
        """Remove given student from the school."""
        response = self.delete('/students/{0}'.format(id))
        _check_json_response_status(response)
        return response.json()

    # Not tested.
    def updateStudent(self, id, **kwargs):
        """Update student's account information.

        Args:
            id: Student ID.
            kwargs: The following parameters are allowed:

                    ======= =================
                    name    Student name.
                    surname Student surname.
                    passwd  Student password.
                    ======= =================

        You may provide string parameter 'raw' instead of key-values.
        It must be well formed JSON string with above fields.
        """
        if 'raw' in kwargs:
            kwargs = kwargs['raw']
        response = self.put('/students/{0}'.format(id), data=kwargs)
        _check_json_response_status(response)
        return response.json()

    def getUserInfo(self):
        """Return current user account information."""
        response = self.get('/userinfo')
        _check_json_response_status(response)
        return response.json()

    def getUserAccountPage(self):
        s = self._session_cookie.find('=')
        e = self._session_cookie.find(';')
        cid = self._session_cookie[s + 1:e]
        return self._url('/user', use_root=True), cid

    def linkFacebookAccount(self, user_id):
        response = self.post('/link_facebook', data={'userId': user_id})
        _check_json_response_status(response)
        return response.json()
