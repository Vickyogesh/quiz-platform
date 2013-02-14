from .exceptions import QuizCoreError
from .db import QuizDb


class QuizCore(object):
    """ Core quiz logic. """

    def __init__(self, settings):
        self.db = QuizDb(settings)

    def getUserAndAppInfo(self, username, appkey):
        return self.db.getInfo(username, appkey)

    def getQuestionList(self, topic_id, lang='it', num=40):
        """
        Return list of :num questions.
        Question is represented as a dictionary with the following items:
            id      - question ID in the DB
            text    - question text
            answer  - question answer (True/False)
            image   - image ID to illustrate the question (optional)
            image_bis - image type ID (optional)
        """
        res = self.db.getQuiz(topic_id, lang, num)
        return {'topic': topic_id, 'questions': res}

    # TODO: implement db update with the answers.
    def saveQuizResults(self, id_list, answers):
        if len(id_list) != len(answers):
            raise QuizCoreError('Parameters length mismatch.')

        try:
            for id, answer in zip(id_list, answers):
                int(id), int(answer)
                pass
        except ValueError:
            raise QuizCoreError('Invalid value.')
        pass
