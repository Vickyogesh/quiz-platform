import os, time, requests, sys
from flask import render_template, redirect, url_for, jsonify, session, request, abort, flash
from . import app, quiz_b, quiz_cqc, quiz_am, quiz_cde, quiz_rev
from instagram.client import InstagramAPI
from flask_babelex import gettext as _
import flask_login

instaConfig = {
    'client_id': os.environ.get('CLIENT_ID'),
    'client_secret': os.environ.get('CLIENT_SECRET'),
    'redirect_uri': os.environ.get('REDIRECT_URI')
}
ig_api = InstagramAPI(**instaConfig)

quiz_b.quiz.init_app(app, quiz_id=1, quiz_year=2011, base_prefix='/ui')
quiz_b.quiz.init_app(app, quiz_id=3, quiz_year=2013, base_prefix='/ui')
quiz_b.quiz.init_app(app, quiz_id=50, quiz_year=2016, base_prefix='/ui',
                     no_url_year=True, main=True)

quiz_cqc.quiz.init_app(app, quiz_id=2, quiz_year=2011, base_prefix='/ui',
                       no_url_year=True)

quiz_am.quiz.init_app(app, quiz_id=4, quiz_year=2014, base_prefix='/ui',
                      no_url_year=True)
quiz_cde.quiz.init_app(app, quiz_id=5, quiz_year=2015, base_prefix='/ui',
                       no_url_year=True, year_in_title=False)

quiz_rev.quiz.init_app(app, quiz_id=60, quiz_year=2016, base_prefix='/ui',
                       no_url_year=True, year_in_title=False)


@app.route('/')
def index():
    return redirect(url_for('b2016.index'))


@app.route('/ui/policy')
def policy():
    return render_template('policy.html')


@app.route('/instagram_login')
def instagram_login():
    url = ig_api.get_authorize_url()
    return redirect(url)


@app.route('/instagram_callback')
def instagram_callback():
    code = request.args.get('code')
    if code:
        access_token, user = ig_api.exchange_code_for_access_token(code)
        if not access_token:
            abort(404)
        from .access import current_user
        # requesting instagram account link
        if current_user.get_id():
            res = app.account.linkInstgramAccount(user['id'])
            # TODO: what if res is not successful
            current_user.account['ig_id'] = user['id']
            redirect_url = session['request_url'] + 'fmenu'
            flash(_('Your account successfully linked with Instagram'), category='success')
            return redirect(redirect_url)

        else:  # requesting login
            redirect_url = requests.Request('GET',
                                            session['request_url'],
                                            params=dict(ig_user=user['id'])).prepare().url
            return redirect(redirect_url)
    else:
        return 'No code provided'
