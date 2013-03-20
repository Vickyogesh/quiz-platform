from .db.quizdb import QuizDb


class QuizCore(object):
    """ Core quiz logic. """

    def __init__(self, settings):
        self.db = QuizDb(settings)

    def getUserAndAppInfo(self, username, appkey):
        return self.db.getInfo(username, appkey)

    def getQuestionList(self, topic_id, user_id, lang='it'):
        """ Return list of Quiz questions.

        Args:
            topic_id:  Topic ID from which get questions for the Quiz.
            user_id:   User ID for whom Quiz is generated.
            lang:      Question language. Can be: (it, fr, de).

        Question is represented as a dictionary with the following items:
            id        - question ID in the DB
            text      - question text
            answer    - question answer (True/False)
            image     - image ID to illustrate the question (optional)
            image_bis - image type ID (optional)
        """
        res = self.db.getQuiz(topic_id, user_id, lang)
        return {'topic': topic_id, 'questions': res}

    def saveQuizResults(self, user_id, topic_id, id_list, answers):
        """ Save quiz result for the user.

        Args:
            user_id:    ID of the user for whom need to save the quiz.
            questions:  List of the quesions IDs.
            answers:    List of questions' answers.

        Raises:
            QuizCoreError

        .. note::
           questions and answers must have tha same length.
        """
        self.db.saveQuizResult(user_id, topic_id, id_list, answers)

    def createExam(self, user_id, lang):
        return self.db.createExam(user_id, lang)

    def saveExam(self, exam_id, questions, answers):
        self.db.saveExam(exam_id, questions, answers)

    def getUserStat(self, user, lang):
        return self.db.getUserStat(user, lang)

    def getErrorReview(self, user, lang):
        res = self.db.getErrorReview(user, lang)
        return {'questions': res}

    def saveErrorReview(self, user, id_list, answers):
        self.db.saveErrorReview(user, id_list, answers)

    def getExamList(self, user_id):
        return self.db.getExamList(user_id)

    def getExamInfo(self, exam_id, lang):
        return self.db.getExamInfo(exam_id, lang)
