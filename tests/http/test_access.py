# to use tests_common
import os.path
import sys
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import requests
import unittest
import json
from sqlalchemy import create_engine, text
from tests_common import cleanupdb_onSetup, cleanupdb_onTearDown
from tests_common import db_uri, url, createAuthFor, HttpStatusTest
from tests_common import cleanupdb_onSetupAccDb, cleanupdb_onTearDownAccDb


def http_get(path):
    return requests.get(url(path))


def http_post(path):
    return requests.post(url(path))


def http_del(path):
    return requests.delete(url(path))


# Test: access to the API for various types of users.
#@unittest.skip("Need to review http errors")
class HttpAccessTest(HttpStatusTest):
    def setUp(self):
        self.engine = create_engine(db_uri, echo=False)
        cleanupdb_onSetup(self.engine)
        cleanupdb_onSetupAccDb(self, drop_users=True, add_users=True)

    def tearDown(self):
        self.engine.dispose()
        cleanupdb_onTearDown(self.engine)
        cleanupdb_onTearDownAccDb(self)

    # Check: unauthorized access to the API
    def test_noauth(self):
        self.assertHttp_Unauthorized(http_get('/quiz/1'))
        self.assertHttp_Unauthorized(http_post('/quiz/1'))

        self.assertHttp_Unauthorized(http_get('/student'))
        self.assertHttp_Unauthorized(http_get('/student/me'))
        self.assertHttp_Unauthorized(http_get('/student/12'))

        self.assertHttp_Unauthorized(http_get('/errorreview'))
        self.assertHttp_Unauthorized(http_post('/errorreview'))

        self.assertHttp_Unauthorized(http_get('/exam'))
        self.assertHttp_Unauthorized(http_get('/exam/1'))
        self.assertHttp_Unauthorized(http_post('/exam/1'))

        self.assertHttp_Unauthorized(http_get('/student/me/exam'))
        self.assertHttp_Unauthorized(http_get('/student/1/exam'))

        self.assertHttp_Unauthorized(http_get('/student/me/topicerrors/1'))
        self.assertHttp_Unauthorized(http_get('/student/1/topicerrors/1'))

        self.assertHttp_Unauthorized(http_get('/admin/schools'))
        self.assertHttp_Unauthorized(http_post('/admin/newschool'))
        self.assertHttp_Unauthorized(http_del('/admin/school/1'))
        self.assertHttp_Unauthorized(http_post('/admin/school/1'))

        self.assertHttp_Unauthorized(http_get('/school/me/students'))
        self.assertHttp_Unauthorized(http_get('/school/1/students'))
        self.assertHttp_Unauthorized(http_post('/school/me/newstudent'))
        self.assertHttp_Unauthorized(http_post('/school/1/newstudent'))
        self.assertHttp_Unauthorized(http_del('/school/1/student/1'))
        self.assertHttp_Unauthorized(http_del('/school/me/student/1'))
        self.assertHttp_Unauthorized(http_post('/school/1/student/1'))

    ### Test access privileges

    def _authFor(self, utype):
        req = requests.Session()
        r = req.get(url('/authorize'))
        nonce = r.json()['nonce']
        auth = json.dumps(createAuthFor(utype, nonce))
        headers = {'content-type': 'application/json'}
        r = req.post(url('/authorize'), data=auth, headers=headers)
        self.assertHttp_Ok(r)
        return r.json()['user']['id'], req

    # Check avaliable API for student
    def test_student(self):
        uid, req = self._authFor('student')

        self.assertHttp_Ok(req.get(url('/quiz/1')))
        self.assertHttp_NotForbidden(req.post(url('/quiz/1')))

        self.assertHttp_Ok(req.get(url('/student')))
        self.assertHttp_Ok(req.get(url('/student/me')))
        self.assertHttp_Ok(req.get(url('/student/' + str(uid))))
        self.assertHttp_Forbidden(req.get(url('/student/2')))

        self.assertHttp_Ok(req.get(url('/errorreview')))
        self.assertHttp_NotForbidden(req.post(url('/errorreview')))

        r = req.get(url('/exam'))
        self.assertHttp_Ok(r)
        exam_id = r.json()['exam']['id']
        self.assertHttp_Ok(req.get(url('/exam/%d' % exam_id)))
        self.assertHttp_NotForbidden(req.post(url('/exam/%d' % exam_id)))

        self.assertHttp_Ok(req.get(url('/student/me/exam')))
        self.assertHttp_Ok(req.get(url('/student/%d/exam' % uid)))
        self.assertHttp_Forbidden(req.get(url('/student/2/exam')))

        self.assertHttp_Ok(req.get(url('/student/me/topicerrors/1')))
        self.assertHttp_Ok(req.get(url('/student/%d/topicerrors/1' % uid)))
        self.assertHttp_Forbidden(req.get(url('/student/2/topicerrors/1')))

        self.assertHttp_Forbidden(req.get(url('/admin/schools')))
        self.assertHttp_Forbidden(req.post(url('/admin/newschool')))
        self.assertHttp_Forbidden(req.delete(url('/admin/school/1')))
        self.assertHttp_Forbidden(req.post(url('/admin/school/1')))

        self.assertHttp_Forbidden(req.get(url('/school/me/students')))
        self.assertHttp_Forbidden(req.get(url('/school/1/students')))
        self.assertHttp_Forbidden(req.post(url('/school/me/newstudent')))
        self.assertHttp_Forbidden(req.post(url('/school/1/newstudent')))
        self.assertHttp_Forbidden(req.delete(url('/school/1/student/1')))
        self.assertHttp_Forbidden(req.delete(url('/school/me/student/1')))
        self.assertHttp_Forbidden(req.post(url('/school/1/student/1')))

    def _resetGuest(self):
        self.engine.execute(text("UPDATE guest_access SET num_requests=0"))

    # Check avaliable API for guest
    def test_guest(self):
        uid, req = self._authFor('guest')

        # We have to reset number of requests for guest
        # to prevent blocking after 10 requests
        self._resetGuest()

        self.assertHttp_Ok(req.get(url('/quiz/1')))
        self.assertHttp_NotForbidden(req.post(url('/quiz/1')))

        self.assertHttp_Ok(req.get(url('/student')))
        self.assertHttp_Ok(req.get(url('/student/me')))
        self.assertHttp_Ok(req.get(url('/student/' + str(uid))))
        self.assertHttp_Forbidden(req.get(url('/student/2')))

        self.assertHttp_Ok(req.get(url('/errorreview')))
        self.assertHttp_NotForbidden(req.post(url('/errorreview')))

        self._resetGuest()
        r = req.get(url('/exam'))
        self.assertHttp_Ok(r)
        exam_id = r.json()['exam']['id']
        self.assertHttp_Ok(req.get(url('/exam/%d' % exam_id)))
        self.assertHttp_NotForbidden(req.post(url('/exam/%d' % exam_id)))

        self.assertHttp_Ok(req.get(url('/student/me/exam')))
        self.assertHttp_Ok(req.get(url('/student/%d/exam' % uid)))
        self.assertHttp_Forbidden(req.get(url('/student/2/exam')))

        self.assertHttp_Ok(req.get(url('/student/me/topicerrors/1')))
        self.assertHttp_Ok(req.get(url('/student/%d/topicerrors/1' % uid)))
        self.assertHttp_Forbidden(req.get(url('/student/2/topicerrors/1')))

        self._resetGuest()
        self.assertHttp_Forbidden(req.get(url('/admin/schools')))
        self.assertHttp_Forbidden(req.post(url('/admin/newschool')))
        self.assertHttp_Forbidden(req.delete(url('/admin/school/1')))
        self.assertHttp_Forbidden(req.post(url('/admin/school/1')))

        self.assertHttp_Forbidden(req.get(url('/school/me/students')))
        self.assertHttp_Forbidden(req.get(url('/school/1/students')))
        self.assertHttp_Forbidden(req.post(url('/school/me/newstudent')))
        self.assertHttp_Forbidden(req.post(url('/school/1/newstudent')))
        self.assertHttp_Forbidden(req.delete(url('/school/1/student/1')))
        self.assertHttp_Forbidden(req.delete(url('/school/me/student/1')))
        self.assertHttp_Forbidden(req.post(url('/school/1/student/1')))

    # Check avaliable API for school
    def test_school(self):
        uid, req = self._authFor('school')

        self.assertHttp_Forbidden(req.get(url('/quiz/1')))
        self.assertHttp_Forbidden(req.post(url('/quiz/1')))

        self.assertHttp_Forbidden(req.get(url('/student')))
        self.assertHttp_Forbidden(req.get(url('/student/me')))
        self.assertHttp_Ok(req.get(url('/student/1')))

        # student from another school (school guest)
        self.assertHttp_Forbidden(req.get(url('/student/2')))

        self.assertHttp_Forbidden(req.get(url('/errorreview')))
        self.assertHttp_Forbidden(req.post(url('/errorreview')))

        self.assertHttp_Forbidden(req.get(url('/exam')))
        self.assertHttp_NotForbidden(req.get(url('/exam/1')))
        self.assertHttp_Forbidden(req.post(url('/exam/1')))

        self.assertHttp_Forbidden(req.get(url('/student/me/exam')))
        self.assertHttp_Ok(req.get(url('/student/1/exam')))
        self.assertHttp_Forbidden(req.get(url('/student/2/exam')))

        # student from another school (school guest)
        self.assertHttp_Forbidden(req.get(url('/student/2/exam')))

        self.assertHttp_NotForbidden(req.get(url('/student/me/topicerrors/1')))
        self.assertHttp_NotForbidden(req.get(url('/student/1/topicerrors/1')))

        self.assertHttp_Forbidden(req.get(url('/student/2/topicerrors/1')))

        self.assertHttp_Forbidden(req.get(url('/admin/schools')))
        self.assertHttp_Forbidden(req.post(url('/admin/newschool')))
        self.assertHttp_Forbidden(req.delete(url('/admin/school/1')))
        self.assertHttp_Forbidden(req.post(url('/admin/school/1')))

        self.assertHttp_Ok(req.get(url('/school/me/students')))
        self.assertHttp_Ok(req.get(url('/school/1/students')))
        self.assertHttp_NotForbidden(req.post(url('/school/me/newstudent')))
        self.assertHttp_NotForbidden(req.post(url('/school/1/newstudent')))
        self.assertHttp_NotForbidden(req.delete(url('/school/1/student/1')))
        self.assertHttp_NotForbidden(req.delete(url('/school/me/student/1')))
        self.assertHttp_NotForbidden(req.post(url('/school/1/student/1')))

    # Check avaliable API for admin
    def test_admin(self):
        uid, req = self._authFor('admin')

        self.assertHttp_Forbidden(req.get(url('/quiz/1')))
        self.assertHttp_Forbidden(req.post(url('/quiz/1')))

        self.assertHttp_Forbidden(req.get(url('/student')))
        #self.assertHttp_Forbidden(req.get(url('/student/me')))
        self.assertHttp_Forbidden(req.get(url('/student/1')))
        self.assertHttp_Forbidden(req.get(url('/student/2')))

        self.assertHttp_Forbidden(req.get(url('/errorreview')))
        self.assertHttp_Forbidden(req.post(url('/errorreview')))

        self.assertHttp_Forbidden(req.get(url('/exam')))
        self.assertHttp_Forbidden(req.get(url('/exam/1')))
        self.assertHttp_Forbidden(req.post(url('/exam/1')))

        self.assertHttp_Forbidden(req.get(url('/student/1/exam')))
        self.assertHttp_Forbidden(req.get(url('/student/2/exam')))

        self.assertHttp_Forbidden(req.get(url('/student/1/topicerrors/1')))

        self.assertHttp_Ok(req.get(url('/admin/schools')))
        self.assertHttp_NotForbidden(req.post(url('/admin/newschool')))
        self.assertHttp_NotForbidden(req.delete(url('/admin/school/1')))
        self.assertHttp_NotForbidden(req.post(url('/admin/school/1')))

        self.assertHttp_NotForbidden(req.get(url('/school/1/students')))
        self.assertHttp_NotForbidden(req.post(url('/school/1/newstudent')))
        self.assertHttp_NotForbidden(req.delete(url('/school/1/student/1')))
        self.assertHttp_NotForbidden(req.post(url('/school/1/student/1')))

        #self.assertHttp_Forbidden(req.get(url('/student/me/exam')))
        #self.assertHttp_Forbidden(req.get(url('/student/me/topicerrors/1')))
        #self.assertHttp_Forbidden(req.get(url('/school/me/students')))
        #self.assertHttp_Forbidden(req.post(url('/school/me/newstudent')))
        #self.assertHttp_Forbidden(req.delete(url('/school/me/student/1')))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(HttpAccessTest))
    return suite

if __name__ == '__main__':
    unittest.main()
