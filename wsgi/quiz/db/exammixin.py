import random
from sqlalchemy import select, text, func


class ExamMixin(object):
    """ Mixin for working with exams. Used in QuizDb. """
    def __init__(self):

        # Get chapters info: priority and chapter's questions' id range.
        query = text('SELECT priority, min_id, max_id FROM chapters')
        self.__stmt_ch_info = query.compile(self.engine)

    # TODO: maybe create stored procedire to build list of questions?
    def __generate_idList(self):
        id_list = []

        # Create list of exam questions.
        # At first, we get info about chapters: chapter priority,
        # min question ID for the chapter and max question ID for the chapter.
        # Example:
        #
        # | priority | min_id  |  max_id
        # |----------+-----+------
        # |     1    |    0    |  100
        # |     2    |   101   |  200
        #
        # This means what for row 1 we need select one question in the range
        # [0 - 100] and for row 2 we need select two (random) questions
        # in the range [101 - 200].
        res = self.conn.execute(self.__stmt_ch_info)
        for row in res:
            min_id = row[1]
            max_id = row[2]
            delta = max_id - min_id

            # Create random ID in the range [min_id - max_id]
            for i in xrange(row[0]):
                id_list.append(int(min_id + delta * random.random()))

        return id_list

    def getExam(self, lang):
        """ Return list of questons for exam.

        Args:
            lang: Questions languange.

        Retuns:
            List of dict objects with the following fields:
               * id         - question ID
               * text       - question text
               * answer     - question answer (True=1/False=0)
               * image      - image ID (optional)
               * image_bis  - image type (optional)
        """

        id_list = self.__generate_idList()

        q = self.questions

        if lang == 'de':
            txt_lang = q.c.text_de
        elif lang == 'fr':
            txt_lang = q.c.text_fr
        else:
            txt_lang = q.c.text

        s = select([q], q.c.id.in_(id_list)).order_by(func.rand())
        res = self.conn.execute(s)

        # TODO: maybe preallocate with exam = [None] * 40?
        exam = []
        for row in res:
            d = {
                'id': row[q.c.id],
                'text': row[txt_lang],
                'answer': row[q.c.answer],
                'image': row[q.c.image],
                'image_bis': row[q.c.image_part]
            }
            self._aux_question_delOptionalField(d)
            exam.append(d)

        return exam
