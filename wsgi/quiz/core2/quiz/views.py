from flask import render_template, session, request, url_for, redirect
from ..bp import core2
from .logic import QuizCore
from ..meta import get_quiz_meta, get_quiz_name
from flask_login import current_user, login_required

q = QuizCore()


@core2.route("/quiz", methods=['GET'])
@login_required
def get_quiz():
    quiz_type = request.args.get('quiz_type')
    force = request.args.get('force', False)
    topic_id = request.args.get('topic')
    topic_lst = request.args.get('t_lst')
    exclude = request.args.get('exclude', None)
    ai = request.args.get('ai', None)

    if exclude is not None:
        exclude = [int(x) for x in exclude.split(',')]
    if topic_lst is not None:
        topic_lst = [int(t) for t in topic_lst.split(',')]

    if not ai:
        quiz = q.getQuiz(quiz_type, current_user.account_id, topic_id, 'it', force, exclude=exclude, topic_lst=topic_lst)
    else:
        quiz = q.get_ai_quiz(quiz_type, current_user.account_id, topic_id, 'it', force, exclude=exclude, topic_lst=topic_lst)

    return render_template('common_quiz.html', quiz_meta=get_quiz_meta(quiz_type), quiz=quiz,
                           user={'account': current_user.account},
                           urls={'back': '/ui/' + get_quiz_name(quiz_type) + '/fmenu', 'image': '/img/',
                                 'quiz': url_for('api.create_quiz', topic=0)[:-1],
                                 'ai_answer': url_for('api.post_ai_answer'),
                                 'ai_question': url_for('api.get_ai_question'),
                                 })


@core2.route("/session_clean", methods=['GET'])
def session_clean():
    session.clear()
    return redirect(request.url_root)

