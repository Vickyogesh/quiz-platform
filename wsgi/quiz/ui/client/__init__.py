from . import menu
from . import quiz
from . import exam
from . import statistics


def register_views(bp):
    bp.route('/c/menu')(menu.Menu.get_view())
    bp.route('/c/menu/quiz')(menu.MenuQuiz.get_view())
    bp.route('/c/quiz/<int:topic>')(quiz.Quiz.get_view())
    bp.route('/c/review')(quiz.Review.get_view())
    bp.route('/c/exam')(exam.Exam.get_view())
    bp.route('/c/exam_review/<int:id>')(exam.ExamReview.get_view())

    view = statistics.Statistics.get_view()
    bp.route('/c/statistics', defaults={'uid': 'me'})(view)
    bp.route('/c/statistics/<uid:uid>')(view)
    bp.route('/c/statistics/<uid:uid>/topic/<int:topic_id>')(
        statistics.StatisticsTopic.get_view())
    bp.route('/c/statistics/<uid:uid>/exams/<range>')(
        statistics.StatisticsExams.get_view())
