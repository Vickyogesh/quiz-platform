from werkzeug.routing import Rule
from quiz.servicebase import ServiceBase
from werkzeug.exceptions import BadRequest
from .servicebase import JSONResponse


class QuizService(ServiceBase):
    """ Quiz web service. """

    def __init__(self, config):
        super(QuizService, self).__init__(config)
        self.urls.add(Rule('/quiz/<int:topic>',
                      methods=['GET'],
                      endpoint='onQuizGet'))
        self.urls.add(Rule('/quiz/<int:topic>',
                      methods=['POST'],
                      endpoint='onQuizSave'))
        self.urls.add(Rule('/errorreview',
                      methods=['GET'],
                      endpoint='onErrorReviewGet'))
        self.urls.add(Rule('/errorreview',
                      methods=['POST'],
                      endpoint='onErrorReviewSave'))
        self.urls.add(Rule('/student',
                      methods=['GET'],
                      endpoint='onStudentStat'))
        self.urls.add(Rule('/student/<uid:user>',
                      methods=['GET'],
                      endpoint='onStudentStat'))
        self.urls.add(Rule('/exam', methods=['GET'],
                      endpoint='onCreateExam'))
        self.urls.add(Rule('/exam/<int:id>',
                      methods=['POST'],
                      endpoint='onSaveExam'))
        self.urls.add(Rule('/exam/<int:id>',
                      methods=['GET'],
                      endpoint='onGetExamInfo'))
        self.urls.add(Rule('/student/<uid:user>/exam',
                      methods=['GET'],
                      endpoint='onStudentExams'))

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
