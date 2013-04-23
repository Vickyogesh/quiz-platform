# locust --host http://quizplatformtest-editricetoni.rhcloud.com
import hashlib
import json
from random import randint
from locust import Locust, TaskSet, task


def _createDigest(nonce, username, passwd):
    m = hashlib.md5()
    m.update('%s:%s' % (username, passwd))
    ha1 = m.hexdigest()
    m = hashlib.md5()
    m.update('%s:%s' % (nonce, ha1))
    return m.hexdigest()


def createAuthData(nonce, login, passwd):
    app_id = '32bfe1c505d4a2a042bafd53993f10ece3ccddca'
    return {
        'nonce': nonce,
        'appid': app_id,
        'login': login,
        'digest': _createDigest(nonce, login, passwd)
    }


class QuizTastSet(TaskSet):
    """Base class for quiz tasks.

    It provides authorization feature
    and also helper methods to process responses.
    """

    # See fill.py to check used id limits.
    def _create_login_data(self):
        school = randint(1, 40)
        user = randint(1, 140)
        login = 'user_%d_%d' % (school, user)
        self.login = login
        return login, login

    def _auth(self):
        login, passwd = self._create_login_data()
        data = self.client.get('/v1/authorize').json
        data = json.dumps(createAuthData(data['nonce'], login, passwd))
        self.checked_post('/v1/authorize', data=data)

    def checked_get(self, *args, **kwargs):
        """Send GET request and check response result.

        This mthod expects that response provides JSON string
        with at least 'status'=200 filed.

        Returns response JSON if 'status' is 200 or None.
        """
        kwargs['catch_response'] = True
        data = None
        with self.client.get(*args, **kwargs) as r:
            try:
                if r.json['status'] != 200:
                    r.failure("%s %s: [GET] Wrong status [%s]" %
                              (self.login, args[0], r.content))
                else:
                    data = r.json
            except Exception:
                r.failure("%s %s: [GET] Not a JSON [%s]" %
                          (self.login, args[0], r.content))
            return data

    def checked_post(self, *args, **kwargs):
        """Send POST request and check response result.

        This mthod expects that response provides JSON string
        with at least 'status'=200 filed.

        Returns response JSON if 'status' is 200 or None.
        """
        kwargs['catch_response'] = True
        kwargs['headers'] = self.headers
        post_data = kwargs.get('data', None)
        if isinstance(post_data, dict):
            kwargs['data'] = json.dumps(post_data)
        data = None
        with self.client.post(*args, **kwargs) as r:
            try:
                if r.json['status'] != 200:
                    r.failure("%s %s: [POST] Wrong status [%s]" %
                              (self.login, args[0], r.content))
                else:
                    data = r.json
            except Exception:
                r.failure("%s %s: [POST] Not a JSON [%s]" %
                          (self.login, args[0], r.content))
            return data

    def on_start(self):
        self.headers = {'content-type': 'application/json'}
        self._auth()
        print "auth %s" % self.login


class StudentBehaviour(QuizTastSet):
    @task
    def quiz(self):
        qid = randint(1, 45)
        json = self.checked_get('/v1/quiz/%d' % qid)
        q = json['questions']

        questions = [x['id'] for x in q]
        answers = [randint(0, 1) for x in xrange(len(questions))]
        result = {'questions': questions, 'answers': answers}

        self.checked_post('/v1/quiz/%d' % qid, data=result)

    @task
    def error_review(self):
        json = self.checked_get('/v1/errorreview')
        q = json['questions']

        questions = [x['id'] for x in q]
        if questions:
            answers = [randint(0, 1) for x in xrange(len(questions))]
            result = {'questions': questions, 'answers': answers}
            self.checked_post('/v1/errorreview', data=result)

    @task
    def student_stat(self):
        self.checked_get('/v1/student/me')


class QuizUser(Locust):
    # min_wait = 5000
    # max_wait = 9000
    task_set = StudentBehaviour
