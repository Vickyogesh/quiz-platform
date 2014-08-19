from flask import url_for, request, session, abort
from ..page import PageModel, ClientPage
from ..babel import gettext
from ... import app, access


############################################################
# Models
############################################################

class ExamModel(PageModel):
    exam_meta = None

    def on_request(self, *args, **kwargs):
        exam_type = request.args.get('exam_type', None)
        data = app.core.createExam(self.page.quiz_id, self.page.uid,
                                   self.page.lang, exam_type)
        self.page.urls = {
            'back': url_for('.client_menu'),
            'image': url_for('img_file', filename=''),
            'exam': url_for('api.save_exam', id=0)[:-1],
            'exam_review': url_for('.client_exam_review', id=0)[:-1]
        }

        if 'fb_id' in access.current_user.account:
            fb_data = {
                'id': access.current_user.account['fb_id'],
                'text': gettext('Number of errors in exam: %%(num)s'),
                'description': 'Quiz Patente',
                'school_title': session.get('extra_school_name'),
                'school_link': session.get('extra_school_url'),
                'school_logo_url': session.get('extra_school_logo_url')
            }
            fb_data = dict((k, v) for k, v in fb_data.iteritems() if v)
        else:
            fb_data = None
        return self.page.render(exam=data, fb_data=fb_data,
                                exam_meta=self.exam_meta)


class BExamModel(ExamModel):
    template = 'ui/b/exam.html'
    exam_meta = {'max_errors': 4, 'total_time': 1800}


class CqcExamModel(ExamModel):
    template = 'ui/cqc/exam.html'
    exam_meta = {'max_errors': 6, 'total_time': 7200}


class ScooterExamModel(ExamModel):
    template = 'ui/scooter/exam.html'
    exam_meta = {'max_errors': 3, 'total_time': 1500}


class ExamReviewModel(PageModel):
    template = 'ui/common_exam_review.html'

    def on_request(self, id):
        info = app.core.getExamInfo(id, self.page.lang)
        if info['student']['id'] != access.current_user.account_id:
            abort(404)
        self.page.urls = {'back': url_for('.client_menu')}
        return self.page.render(exam=info)


############################################################
# View
############################################################

class Exam(ClientPage):
    models = {
        'b':  BExamModel,
        'cqc':  CqcExamModel,
        'scooter':  ScooterExamModel
    }


class ExamReview(ClientPage):
    models = {'':  ExamReviewModel}
