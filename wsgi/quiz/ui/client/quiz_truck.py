from flask import session, current_app, redirect, url_for, request
from sqlalchemy import select, and_
from ..page import access, PageModel, PagesMetadata
from .views import ClientPage
from .models import MenuModel, QuizMenuModel, ExamModel, StatisticsModel
from ..util import QUIZ_TITLE
from ...core import exammixin


class SubLicenseModel(PageModel):
    template = 'ui/truck/truck_sublicense.html'

    def update_render_context(self, ctx):
        types = [{'id': x, 'title': QUIZ_TITLE[x]} for x in xrange(5, 12)]
        ctx['sublicense'] = types


class SubLicenseView(ClientPage):
    rules = ({'rule': '/c/truck/sublicense'},)
    default_model = SubLicenseModel


class TruckModel(MenuModel):
    """Truck menu handles sub license value.

    It redirects to sub license select page if no value is found.
    """
    template = 'ui/truck/menu_client.html'

    def on_request(self, *args, **kwargs):
        user = access.current_user

        try:
            sub_license = int(request.args.get('id'))
        except (ValueError, TypeError):
            sub_license = None

        user_type = 0
        if user.is_student or user.is_guest:
            user_type = 1
        elif user.is_school:
            user_type = 2

        # If sub_license is not specified in URL query then we try to get it
        # from session and then from DB.
        if sub_license is None:
            if 'sub_license' not in session:
                t = current_app.core.truck_last_sublicense

                sql = select([t.c.sublicense]).where(and_(
                    t.c.user_id == user.account_id, t.c.user_type == user_type))

                res = current_app.core.engine.execute(sql).fetchone()
                if res is not None:
                    sub_license = res[0]
            else:
                sub_license = session['sub_license']

        # If sub_license is specified in URL query then we save it in session
        # and DB. Session one will be used by other pages and DB one will be
        # used on next login.
        else:
            t = current_app.core.truck_last_sublicense
            add = 'ON DUPLICATE KEY UPDATE sublicense=sublicense'
            sql = t.insert(append_string=add).values(user_id=user.account_id,
                                                     user_type=user_type,
                                                     sublicense=sub_license)
            current_app.core.engine.execute(sql)
            session['sub_license'] = sub_license
            session['quiz_id'] = sub_license

        # If sub_license is not found in session and DB then we redirect
        # to page with sub_license choices.
        if sub_license is None:
            return redirect(url_for('.client_sub_license'))

        # Otherwise show menu.
        return MenuModel.on_request(self, *args, **kwargs)


class TruckQuizMenuModel(QuizMenuModel):
    template = 'ui/truck/menu_quiz.html'


class TruckStatisticsModel(StatisticsModel):
    def on_request(self, *args, **kwargs):
        self.exam_meta = exammixin.exam_meta[session['quiz_id']]
        return StatisticsModel.on_request(self, *args, **kwargs)


class TruckExamModel(ExamModel):
    template = 'ui/truck/exam.html'

    def update_render_context(self, ctx):
        ctx['exam_data'] = self.exam_meta

    def on_request(self, *args, **kwargs):
        self.exam_meta = exammixin.exam_meta[session['quiz_id']]
        return ExamModel.on_request(self, *args, **kwargs)


class TruckPagesMetadata(PagesMetadata):
    name = 'truck'
    standard_page_models = {
        'menu': TruckModel,
        'menu_quiz': TruckQuizMenuModel,
        'exam': TruckExamModel,
        'stat': TruckStatisticsModel
    }

    extra_views = [SubLicenseView]
