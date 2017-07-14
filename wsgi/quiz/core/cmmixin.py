from sqlalchemy import and_
from flask import jsonify


class ContentManagerMixin(object):

    def getQuestion(self, quiz_id, question_id):
        q = self.questions

        sql = q.select().where(and_(q.c.quiz_type == quiz_id, q.c.id == question_id))

        res = self.engine.execute(sql).fetchone()
        if res is None:
            return 'null'

        info = {'id': res[q.c.id], 'text': res[q.c.text],
                'explanation': res[q.c.explanation], 'image': res[q.c.image]}
        return jsonify(info)

    def setExplanation(self, quiz_id, question_id, explanation):
        q = self.questions

        sql = q.update().where(and_(q.c.quiz_type == quiz_id, q.c.id == question_id))\
            .values(explanation=explanation)
        res = self.engine.execute(sql)
        print res
        return jsonify({'status': 200})