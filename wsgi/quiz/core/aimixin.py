import requests, json
from sqlalchemy import and_, select
from flask import jsonify, current_app


class AiMixin(object):

    def getAiTitle(self, quiz_type, topic_id, lang):

        t = self.topics
        chapter = t.c.chapter_id
        if lang == 'de':
            col = t.c.text_de
        elif lang == 'fr':
            col = t.c.text_fr
        else:
            col = t.c.text
        s = select([col, chapter], and_(t.c.id == topic_id, t.c.quiz_type == quiz_type))
        row = self.engine.execute(s).fetchone()
        return row[col], row[chapter]

    def getAiQuestion(self, data):
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
        q = self.questions

        sql = q.select().where(and_(q.c.quiz_type == data['quiz_type'], q.c.id == ai_res['quest_id']))

        res = self.engine.execute(sql).fetchone()
        if res is None:
            return 'null'

        info = {'id': res[q.c.id], 'text': res[q.c.text], 'answer': res[q.c.answer],
                'explanation': res[q.c.explanation], 'image': res[q.c.image], 'status': 200}
        return info

    def postAiAnswer(self, data):
        """
            Posting answer to guacamole
            :param data:{"quiz_session": "guuy7687hjkhj", "quest_id": 4, "correct": 1, "num_quest": 40}
            :return:{
                        "data": {
                            "progress": 0.06666666666666667,
                            "score": 0.20004213436343657,
                            "status": "in_progress"
                        },
                        "status": 200
                    }
        """
        headers = {'Content-type': 'application/json', 'Accept': 'text/plain'}
        return requests.post(current_app.config["AI_REST_URL"] + "post_answer",
                             data=json.dumps(data), headers=headers).json()