import os, time, requests
from flask import render_template, redirect, url_for, jsonify, session, request, abort, flash
from . import app, quiz_b, quiz_cqc, quiz_am, quiz_cde, quiz_rev
from instagram.client import InstagramAPI

instaConfig = {
    'client_id': os.environ.get('CLIENT_ID'),
    'client_secret': os.environ.get('CLIENT_SECRET'),
    'redirect_uri': None
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


# @app.route('/instagram_connect')
# def instagram_connect():
#     r_url = request.host_url + 'instagram_callback'
#     url = requests.Request('GET', r_url, params=dict(param='arg1')).prepare().url
#     ig_api.redirect_uri = url
#     url = ig_api.get_authorize_url()
#     return redirect(url)


@app.route('/instagram_login')
def instagram_login():
    r_url = request.host_url + 'instagram_callback'
    print(r_url)
    ig_api.redirect_uri = r_url
    url = ig_api.get_authorize_url()
    print(url)
    return redirect(url)


@app.route('/instagram_callback')
def instagram_callback():
    code = request.args.get('code')
    account_id = request.args.get('id')

    print('the parameter', account_id)
    if code:
        access_token, user = ig_api.exchange_code_for_access_token(code)
        if not access_token:
            abort(404)
        from .access import current_user
        # requesting instagram account link
        if account_id and account_id == str(current_user.account_id):
            res = app.account.linkInstgramAccount(user['id'])
            current_user.account['ig_id'] = user['id']
            redirect_url = session['request_url'] + 'fmenu'
            # TODO:redirect to menu page with flashed message success or failure
            flash('link success', category='success')
            return redirect(redirect_url)
        else:  # requesting login
            redirect_url = requests.Request('GET',
                                            session['request_url'],
                                            params=dict(ig_user=user['id'])).prepare().url
            return redirect(redirect_url)
    else:
        return 'No code provided'
