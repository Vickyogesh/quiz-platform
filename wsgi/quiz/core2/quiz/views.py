from flask import render_template, session, request, url_for
from ..bp import core2
from .logic import QuizCore
from ..meta import meta, get_quiz_meta

q = QuizCore(meta)


@core2.route("/quiz", methods=['GET'])
def get_quiz():
    force = request.args.get('force', False)
    topic_id = request.args.get('topic')
    topic_lst = request.args.get('t_lst')
    exclude = request.args.get('exclude', None)

    if exclude is not None:
        exclude = [int(x) for x in exclude.split(',')]
    if topic_lst is not None:
        topic_lst = [int(t) for t in topic_lst.split(',')]

    quiz = q.getQuiz(session['quiz_id'], session['user']['id'], topic_id, 'it', force, exclude=exclude, topic_lst=topic_lst)
    return render_template('common_quiz.html', quiz_meta=get_quiz_meta(session), quiz=quiz,
                           user={'account': session['user']},
                           urls={'back': '/ui/' + session['quiz_name'], 'image': '/img/',
                                 'quiz': url_for('api.create_quiz', topic=0)[:-1]})

