from werkzeug.routing import Rule
from quiz.servicebase import ServiceBase
from werkzeug.exceptions import BadRequest
from .servicebase import JSONResponse


class QuizService(ServiceBase):
    """ Quiz web service. """

    def __init__(self, config):
        super(QuizService, self).__init__(config)
        self._addRules([
            ('GET',   '/quiz/<int:topic>',        'onQuizGet'),
            ('POST',  '/quiz/<int:topic>',        'onQuizSave'),
            ('GET',   '/errorreview',             'onErrorReviewGet'),
            ('POST',  '/errorreview',             'onErrorReviewSave'),
            ('GET',   '/exam',                    'onCreateExam'),
            ('POST',  '/exam/<int:id>',           'onSaveExam'),
            ('GET',   '/exam/<int:id>',           'onGetExamInfo'),
            ('GET',   '/student',                 'onStudentStat'),
            ('GET',   '/student/<uid:user>',      'onStudentStat'),
            ('GET',   '/student/<uid:user>/exam', 'onStudentExams'),
            ('GET',   '/student/<uid:user>/topicerrors/<int:id>', 'onTopicErrors')
        ])

    def _addRules(self, rules):
        for rule in rules:
            self.urls.add(Rule(rule[1], methods=[rule[0]], endpoint=rule[2]))

    def onQuizGet(self, request, topic):
        """ Get 40 questions from the DB and return them to the client. """
        lang = request.args.get('lang', 'it')

        user_id = self.session['user_id']
        quiz = self.core.getQuestionList(topic, user_id, lang)
        return JSONResponse(quiz)

    def onQuizSave(self, request, topic):
        """ Save quiz results. """
        user_id = self.session['user_id']
        data = request.json

        try:
            id_list = data['questions']
            answers = data['answers']
        except KeyError:
            raise BadRequest('Missing parameter.')

        self.core.saveQuizResults(user_id, topic, id_list, answers)
        return JSONResponse()

    def onStudentStat(self, request, user='me'):
        if user == 'me':
            user = self.session['user_id']
        lang = request.args.get('lang', 'it')

        stat = self.core.getUserStat(user, lang)
        return JSONResponse(stat)

    def onErrorReviewGet(self, request):
        user_id = self.session['user_id']
        lang = request.args.get('lang', 'it')

        res = self.core.getErrorReview(user_id, lang)
        return JSONResponse(res)

    def onErrorReviewSave(self, request):
        user_id = self.session['user_id']
        data = request.json

        try:
            id_list = data['questions']
            answers = data['answers']
        except KeyError:
            raise BadRequest('Missing parameter.')

        self.core.saveErrorReview(user_id, id_list, answers)
        return JSONResponse()

    def onCreateExam(self, request):
        user_id = self.session['user_id']
        lang = request.args.get('lang', 'it')
        exam = self.core.createExam(user_id, lang)
        return JSONResponse(exam)

    def onSaveExam(self, request, id):
        data = request.json

        try:
            questions = data['questions']
            answers = data['answers']
        except KeyError:
            raise BadRequest('Missing parameter.')

        self.core.saveExam(id, questions, answers)
        return JSONResponse()

    def onGetExamInfo(self, request, id):
        lang = request.args.get('lang', 'it')
        info = self.core.getExamInfo(id, lang)
        return JSONResponse(info)

    def onStudentExams(self, request, user):
        if user == 'me':
            user = self.session['user_id']
        exams = self.core.getExamList(user)
        return JSONResponse(exams)

    def onTopicErrors(self, request, user, id):
        if user == 'me':
            user = self.session['user_id']
        lang = request.args.get('lang', 'it')
        info = self.core.getTopicErrors(user, id, lang)
        return JSONResponse(info)
