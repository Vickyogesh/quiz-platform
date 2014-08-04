from flask import session, url_for, request
from . import ui
from .common import render_template, check_access, account_url
from .. import access, app


@ui.route('/p/quiz/<int:topic>')
@check_access
@access.be_client_or_guest.require()
def quiz(topic):
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    lang = request.args.get('lang', 'it')
    force = request.args.get('force', False)

    # TODO: what if x is not int?
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        exclude = exclude.split(',')
        exclude = [int(x) for x in exclude]

    quiz = app.core.getQuiz(quiz_type, access.current_user.account_id, topic,
                            lang, force, exclude)

    image_url = url_for('img_file', filename='')
    quiz_url = url_for('api.create_quiz', topic=0)[:-1]

    return render_template('ui/quiz.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           image_url=image_url,
                           quiz_url=quiz_url,
                           user=access.current_user,
                           quiz=quiz,
                           account_url=account_url())


@ui.route('/p/review')
@check_access
@access.be_client_or_guest.require()
def review():
    quiz_name = session['quiz_type_name']
    quiz_type = session['quiz_type']
    uid = access.current_user.account_id
    lang = request.args.get('lang', 'it')

    # TODO: what if x is not int?
    exclude = request.args.get('exclude', None)
    if exclude is not None:
        exclude = exclude.split(',')
        exclude = [int(x) for x in exclude]

    quiz = app.core.getErrorReview(quiz_type, uid, lang, exclude)

    image_url = url_for('img_file', filename='')
    quiz_url = url_for('api.get_error_review')

    return render_template('ui/review.html', quiz_name=quiz_name,
                           back_url=url_for('.menu'),
                           image_url=image_url,
                           quiz_url=quiz_url,
                           user=access.current_user,
                           quiz=quiz,
                           account_url=account_url())
