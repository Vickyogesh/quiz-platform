try:
    import simplejson as json
except ImportError:
    import json

import hashlib
import requests
from datetime import datetime
from werkzeug.http import parse_dict_header
from werkzeug.exceptions import default_exceptions, abort
from werkzeug.http import dump_cookie


def _create_digest(login, passwd):
    m = hashlib.md5()
    m.update('%s:%s' % (login, passwd))
    return m.hexdigest()


# TODO: test me
class RequestProxy(object):
    # Key in the parent session.

    API_SERVER_SESSION_KEY = 'session'
    PARENT_SESSION_KEY = 'accounts.session'

    """This class allows to send HTTP requests and save session data
    inside another session object.
    """
    def __init__(self, server_url, session_func={}, call_save=True):
        """Construct RequestProxy object.

        Args:
            server_url: API server URL.
            session_func: Function which returns session object.
                          It used to save data of session with the
                          API server. If you authorize only with one
                          user then leave it default.
            call_save: Call session_object.save() to save session changes
                       (if save method is provided).

        session_func may be a dic or function like:

            def func():
                reutrn session_object
        """
        self.server_url = server_url
        self.session_func = session_func
        if isinstance(session_func, dict):
            self.is_dict = True
            self.call_save = False
        else:
            self.is_dict = False
            self.call_save = call_save or hasattr(self._session, 'save')

    @property
    def _session(self):
        return self.session_func if self.is_dict else self.session_func()

    # Construct accounts service URL.
    def _url(self, path):
        return self.server_url + path

    # Save cookie in the session for later use.
    def _save_session(self, response):
        if 'session' in response.cookies:
            c = dump_cookie(self.API_SERVER_SESSION_KEY,
                            response.cookies[self.API_SERVER_SESSION_KEY])
            self._session[self.PARENT_SESSION_KEY] = c
            if self.call_save:
                self._session.save()

    @property
    def _session_cookie(self):
        return self._session[self.PARENT_SESSION_KEY]

    def _add_header(self, dest, key, val):
        if 'headers' in dest:
            headers = dest['headers']
            headers[key] = val
        else:
            dest['headers'] = {key: val}

    # TODO: what if we already have 'Cookie' - currently it will be replaced.
    def _apply_session(self, dest):
        if self.PARENT_SESSION_KEY in self._session:
            if self._session_cookie is None:
                return
            self._add_header(dest, 'Cookie', self._session_cookie)

    def get(self, path, **kwargs):
        "Sends a GET request."
        self._apply_session(kwargs)
        r = requests.get(self._url(path), **kwargs)
        self._save_session(r)
        return r

    def post(self, path, **kwargs):
        "Sends a POST request."
        self._apply_session(kwargs)
        if 'data' in kwargs:
            data = kwargs['data']
            if isinstance(data, dict):
                kwargs['data'] = json.dumps(data)
            if 'content-type' not in kwargs:
                self._add_header(kwargs, 'content-type', 'application/json')
        r = requests.post(self._url(path), **kwargs)
        self._save_session(r)
        return r

    def put(self, path, **kwargs):
        "Sends a PUT request."
        self._apply_session(kwargs)
        r = requests.put(self._url(path), **kwargs)
        self._save_session(r)
        return r

    def delete(self, path, **kwargs):
        "Sends a DELETE request."
        self._apply_session(kwargs)
        r = requests.delete(self._url(path), **kwargs)
        self._save_session(r)
        return r


# TODO: test me
class AccountApi(RequestProxy):
    """This class provides accounts service API."""

    def __init__(self, server_url, session_func={}, call_save=True):
        super(AccountApi, self).__init__(server_url, session_func, call_save)

    def _check_response_status(self, response):
        if response.status_code == 200:
            return

        code = response.status_code
        try:
            data = response.json()
        except:
            data = None

        if (data is None or 'description' not in data
           or code not in default_exceptions):
            abort(code)

        raise default_exceptions[code](description=data['description'])

    def get_auth(self):
        """Get auth information from the Account Service.

        Returns: a dict with auth data (currently contains only 'nonce')
        """
        response = self.get('/login')
        hdr = response.headers['WWW-Authenticate']
        hdr = parse_dict_header(hdr[6:])
        return hdr

    def send_auth(self, login, passwd_digest, nonce):
        """Send auth info to the Account Service."""
        hdr = 'QAuth nonce="{0}", username="{1}", response="{2}"'
        hdr = hdr.format(nonce, login, passwd_digest)
        hdr = {'Authenticate': hdr}

        response = self.post('/login', headers=hdr)
        self._check_response_status(response)
        return response.json()

    def login(self, login, passwd):
        """Login to the Account Service."""
        info = self.get_auth()
        passwd_digest = _create_digest(login, passwd)
        passwd_digest = _create_digest(info['nonce'], passwd_digest)
        account = self.send_auth(login, passwd_digest, info['nonce'])
        return account

    def logout(self):
        """Logout from the Account Service."""
        response = self.post('/logout')
        self._check_response_status(response)

    def getSchools(self):
        """Get schools list."""
        response = self.get('/schools')
        self._check_response_status(response)
        return response.json()

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
                kwargs = raw[:-1] + ', "access": {"access_quiz_b": "2150-01-01"}}'
        else:
            if 'access' not in kwargs:
                kwargs['access'] = {'access_quiz_b': '2150-01-01'}

        response = self.post('/schools', data=kwargs)
        self._check_response_status(response)
        return response.json()

    def removeSchool(self, school_id):
        """Remove registered school."""
        response = self.delete('/schools/{0}'.format(school_id))
        self._check_response_status(response)
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
        self._check_response_status(response)
        return response.json()

    def getSchoolStudents(self, school_id, id_list=None):
        if id_list is None:
            url = '/schools/{0}/students'.format(school_id)
        else:
            ids = ','.join(str(x) for x in id_list)
            url = '/schools/{0}/students?id={1}'.format(school_id, ids)
        response = self.get(url)
        self._check_response_status(response)
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
                    login   Student login.
                    passwd  Student passwd.
                    ======= ================

        You may provide string parameter 'raw' instead of key-values.
        It must be well formed JSON string with above fields.
        """
        if 'raw' in kwargs:
            kwargs = kwargs['raw']
        response = self.post('/schools/{0}/students'.format(school_id),
                             data=kwargs)
        self._check_response_status(response)
        return response.json()

    def getStudent(self, id):
        """Get account information for the given student."""
        response = self.get('/students/{0}'.format(id))
        self._check_response_status(response)
        return response.json()

    def removeStudent(self, id):
        """Remove given student from the school."""
        response = self.delete('/students/{0}'.format(id))
        self._check_response_status(response)
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
        self._check_response_status(response)
        return response.json()
