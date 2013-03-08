from werkzeug.routing import Rule
from quiz.servicebase import ServiceBase
from werkzeug.exceptions import BadRequest
from .exceptions import QuizCoreError
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
        self.urls.add(Rule('/exam', methods=['GET'], endpoint='onExamGet'))

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

        try:
            self.core.saveQuizResults(user_id, topic, id_list, answers)
        except QuizCoreError as e:
            raise BadRequest(e.message)
        return JSONResponse()

    def onStudentStat(self, request, user='me'):
        if user == 'me':
            user = self.session['user_id']
        lang = request.args.get('lang', 'it')

        try:
            stat = self.core.getUserStat(user, lang)
        except QuizCoreError as e:
            raise BadRequest(e.message)
        return JSONResponse(stat)

    def onErrorReviewGet(self, request):
        user_id = self.session['user_id']
        lang = request.args.get('lang', 'it')

        try:
            res = self.core.getErrorReview(user_id, lang)
        except QuizCoreError as e:
            raise BadRequest(e.message)
        return JSONResponse(res)

    def onErrorReviewSave(self, request):
        user_id = self.session['user_id']
        data = request.json

        try:
            id_list = data['questions']
            answers = data['answers']
        except KeyError:
            raise BadRequest('Missing parameter.')

        try:
            self.core.saveErrorReview(user_id, id_list, answers)
        except QuizCoreError as e:
            raise BadRequest(e.message)
        return JSONResponse()

    def onExamGet(self, request):
        """ Get exam. """
        lang = request.args.get('lang', 'it')
        exam = self.core.getExam(lang)
        return JSONResponse(exam)
