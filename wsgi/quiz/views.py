from flask import render_template
from . import app, quiz_b, quiz_cqc, quiz_am, quiz_cde

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


@app.route('/ui/policy')
def policy():
    return render_template('policy.html')
