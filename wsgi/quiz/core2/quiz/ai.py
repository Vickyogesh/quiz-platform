import requests
import json
from flask import current_app
from ..models import Question


def getAiQuestion(data):
    """
        Getting question from guacamole rest api
        :param data: {"quiz_type": 50, "u_id": 6, "num_ex": 40, "quiz_session": "guuy7687hjkhj"}
    """
    # {"quest_id": "4","status": 200}
    headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
    ai_res = requests.post(current_app.config["AI_REST_URL"] + "get_question",
                           data=json.dumps(data), headers=headers).json()
    print ai_res
    if ai_res['status'] != 200:
        return ai_res

    res = Question.query.filter_by(id=ai_res['quest_id'], quiz_type=data['quiz_type']).first()
    if res is None:
        return 'null'

    info = {'id': res.id, 'text': res.text, 'answer': res.answer,
            'explanation': res.explanation, 'image': res.image, 'status': 200}
    return info