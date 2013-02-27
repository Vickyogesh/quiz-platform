import json
from werkzeug.wrappers import Response
from werkzeug.routing import Rule
from quiz.servicebase import ServiceBase
from werkzeug.exceptions import BadRequest
from quiz.exceptions import QuizCoreError


class QuizService(ServiceBase):
    """ Quiz web service. """

    def __init__(self, config):
        super(QuizService, self).__init__(config)
        self.urls.add(Rule('/quiz/<int:topic>',
                      methods=['GET'],
                      endpoint='onQuizGet'))
        self.urls.add(Rule('/quiz', methods=['POST'], endpoint='onQuizSave'))
        self.urls.add(Rule('/exam', methods=['GET'], endpoint='onExamGet'))

    # TODO: test more
    # If string is passed instead of list then
    # we suppose what comma delimited string is passed
    # See onQuizSave()
    def _get_param(self, request, name):
        val = request.form.getlist(name)
        if len(val) == 1 and isinstance(val[0], unicode):
            return val[0].split(',')
        return val

    def onQuizGet(self, request, topic):
        """ Get 40 questions from the DB and return them to the client. """
        lang = request.args.get('lang', 'it')

        user_id = self.session['user_id']
        quiz = self.core.getQuestionList(topic, user_id, lang)
        result = json.dumps(quiz, separators=(',', ':'))
        return Response(result, content_type='application/json')

    def onQuizSave(self, request):
        """ Save quiz results. """
        user_id = self.session['user_id']
        id_list = self._get_param(request, 'id')
        answers = self._get_param(request, 'answer')

        if not id_list or not answers:
            raise BadRequest('Missing parameter.')

        try:
            self.core.saveQuizResults(user_id, id_list, answers)
        except QuizCoreError, e:
            raise BadRequest(e.message)

        return Response('ok')

    def onExamGet(self, request):
        """ Get exam. """
        lang = request.args.get('lang', 'it')
        exam = self.core.getExam(lang)
        result = json.dumps(exam, separators=(',', ':'))
        return Response(result, content_type='application/json')
