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
        self.urls.add(Rule('/quiz', methods=['GET'], endpoint='on_quiz_get'))
        self.urls.add(Rule('/quiz', methods=['POST'], endpoint='on_quiz_post'))

    # TODO: test more
    # If string is passed instead of list then
    # we suppose what comma delimited string is passed
    # See on_quiz_post()
    def _get_param(self, request, name):
        val = request.form.getlist(name)
        if len(val) == 1 and isinstance(val[0], unicode):
            return val[0].split(',')
        return val

    def on_quiz_get(self, request):
        """ Get 40 questions from the DB and return them to the client. """
        lang = request.args.get('lang', 'it')

        try:
            topic_id = int(request.args['topic'])
        except ValueError:
            raise BadRequest('Invalid topic value.')
        except BadRequest:
            raise BadRequest('Missing parameter.')

        quiz = self.core.getQuestionList(topic_id, lang)
        result = json.dumps(quiz, separators=(',', ':'))
        return Response(result, content_type='application/json')

    def on_quiz_post(self, request):
        """ Save quiz results. """
        id_list = self._get_param(request, 'id')
        answers = self._get_param(request, 'answer')

        if not len(id_list) or not len(answers):
            raise BadRequest('Missing parameter.')

        try:
            self.core.saveQuizResults(id_list, answers)
        except QuizCoreError, e:
            raise BadRequest(e.message)

        return Response('ok')
