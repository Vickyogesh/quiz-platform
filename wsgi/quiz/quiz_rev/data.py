# coding=utf-8
from flask_babelex import lazy_gettext

subquiz = {
    60: {
        'title': lazy_gettext('Revisioni AM'),
        'exam_meta': {
            'max_errors': 2,
            'total_time': 1200,
            'num_questions': 20,
            'questions_per_chapter': [2, 2, 2, 2, 2, 2, 2, 2, 2, 2]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale',
                'chapters': [[1], [2, 3], [4, 5, 6]],
                'chapter_numbers': [1, 2, 3]
            },
            {
                'text': u'Norme di comportamento per la circolazione sulla strada',
                'chapters': [[7], [8, 9, 10, 11], [12]],
                'chapter_numbers': [4, 5, 6]
            },
            {
                'text': u'Sicurezza e prevenzione degli incidenti',
                'chapters': [[13]],
                'chapter_numbers': [7]
            },
            {
                'text': u'Efficienza e uso del ciclomotore',
                'chapters': [[14, 15]],
                'chapter_numbers': [8]
            },
            {
                'text': u'Comportamenti alla guida e legalità',
                'chapters': [[16], [17]],
                'chapter_numbers': [9, 10]
            }
        ]
    },

    61: {
        'title': lazy_gettext('Revisioni A1 A2 A B1 B BE'),
        'exam_meta': {
            'max_errors': 3,
            'total_time': 1800,
            'num_questions': 30,
            'questions_per_chapter': [3, 3, 3, 3, 3, 3, 3, 3, 3, 3]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale e disposizioni per il conducente',
                'chapters': [[1], [2, 3], [4], [5, 6, 7, 8, 9]],
                'chapter_numbers': [1, 2, 3, 4]
            },
            {
                'text': u'Norme di comportamento sulla strada',
                'chapters': [[10, 11, 12, 13, 14]],
                'chapter_numbers': [5]
            },
            {
                'text': u'Sicurezza e prevenzione degli incidenti',
                'chapters': [[15, 16, 17], [18, 19]],
                'chapter_numbers': [6, 7]
            },
            {
                'text': u'Circolazione dei veicoli e consapevolezza ambientale',
                'chapters': [[20, 21, 22, 23, 24]],
                'chapter_numbers': [8]
            },
            {
                'text': u'Condizioni psico-fisiche del conducente e rispetto della vita',
                'chapters': [[25, 26, 27, 28]],
                'chapter_numbers': [9]
            },
            {
                'text': u'Veicolo sicuro e correttezza di guida',
                'chapters': [[29, 30, 31]],
                'chapter_numbers': [10]
            }
        ]
    },

    62: {
        'title': lazy_gettext('Revisioni C1 (97), C1E (97)'),
        'exam_meta': {
            'max_errors': 3,
            'total_time': 1800,
            'num_questions': 30,
            'questions_per_chapter': [3, 3, 3, 2, 3, 2, 3, 3, 2, 2, 2, 2]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale e disposizioni per il conducente',
                'chapters': [[1], [2, 3], [4], [5, 6, 7, 8, 9]],
                'chapter_numbers': [1, 2, 3, 4]
            },
            {
                'text': u'Norme di comportamento e sicurezza sulla strada',
                'chapters': [[10, 11, 12, 13, 14], [15, 16, 17], [18, 19]],
                'chapter_numbers': [5, 6, 7]
            },
            {
                'text': u'Circolazione dei veicoli e consapevolezza ambientale',
                'chapters': [[20, 21, 22, 23, 24]],
                'chapter_numbers': [8]
            },
            {
                'text': u'Condizioni psico-fisiche del conducente e rispetto della vita',
                'chapters': [[25, 26, 27, 28]],
                'chapter_numbers': [9]
            },
            {
                'text': u'Veicolo sicuro, caricamento adeguato e correttezza di guida',
                'chapters': [[29, 30, 31], [32], [33, 34]],
                'chapter_numbers': [10, 11, 12]
            }
        ]
    },

    63: {
        'title': lazy_gettext('Revisioni C1 C1E C CE'),
        'exam_meta': {
            'max_errors': 3,
            'total_time': 1800,
            'num_questions': 30,
            'questions_per_chapter': [3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 2, 2, 2]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale e disposizioni per il conducente',
                'chapters': [[1], [2, 3], [4], [5, 6, 7, 8, 9]],
                'chapter_numbers': [1, 2, 3, 4]
            },
            {
                'text': u'Norme di comportamento sulla strada e consapevolezza ambientale',
                'chapters': [[10, 11, 12, 13, 14], [15, 16, 17], [18, 19], [20, 21, 22, 23, 24]],
                'chapter_numbers': [5, 6, 7, 8]
            },
            {
                'text': u'Condizioni psico-fisiche del conducente e visibilità nella guida',
                'chapters': [[25, 26, 27, 28], [29]],
                'chapter_numbers': [9, 10]
            },
            {
                'text': u'Normativa sociale nei trasporti professionali',
                'chapters': [[30, 31]],
                'chapter_numbers': [11]
            },
            {
                'text': u'Comportamenti per la sicurezza',
                'chapters': [[32, 33], [34, 35]],
                'chapter_numbers': [12, 13]
            }
        ]
    },

    64: {
        'title': lazy_gettext('Revisioni D1 D1E D DE'),
        'exam_meta': {
            'max_errors': 3,
            'total_time': 1800,
            'num_questions': 30,
            'questions_per_chapter': [3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 2, 2, 2]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale e disposizioni per il conducente',
                'chapters': [[1], [2, 3], [4], [5, 6, 7, 8, 9]],
                'chapter_numbers': [1, 2, 3, 4]
            },
            {
                'text': u'Norme di comportamento sulla strada e consapevolezza ambientale',
                'chapters': [[10, 11, 12, 13, 14], [15, 16, 17], [18, 19], [20, 21, 22, 23, 24]],
                'chapter_numbers': [5, 6, 7, 8]
            },
            {
                'text': u'Condizioni psico-fisiche del conducente e visibilità nella guida',
                'chapters': [[25, 26, 27, 28], [29]],
                'chapter_numbers': [9, 10]
            },
            {
                'text': u'Normativa sociale nei trasporti professionali',
                'chapters': [[30, 31]],
                'chapter_numbers': [11]
            },
            {
                'text': u'Comportamenti per la sicurezza',
                'chapters': [[32, 33], [34, 35, 36]],
                'chapter_numbers': [12, 13]
            }
        ]
    },

    65: {
        'title': lazy_gettext('Revisioni CQC merci'),
        'exam_meta': {
            'max_errors': 4,
            'total_time': 2400,
            'num_questions': 40,
            'questions_per_chapter': [3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 3, 3, 2, 3,
                                      3, 2]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale e disposizioni per il conducente',
                'chapters': [[1], [2, 3], [4], [5, 6, 7, 8, 9]],
                'chapter_numbers': [1, 2, 3, 4]
            },
            {
                'text': u'Norme di comportamento sulla strada e consapevolezza ambientale',
                'chapters': [[10, 11, 12, 13, 14], [15, 16, 17], [18, 19], [20, 21, 22, 23, 24]],
                'chapter_numbers': [5, 6, 7, 8]
            },
            {
                'text': u'Condizioni psico-fisiche del conducente e visibilità nella guida',
                'chapters': [[25, 26, 27, 28], [29]],
                'chapter_numbers': [9, 10]
            },
            {
                'text': u'Normativa sociale nei trasporti professionali',
                'chapters': [[30, 31]],
                'chapter_numbers': [11]
            },
            {
                'text': u'Comportamenti per la sicurezza dei veicoli e del carico',
                'chapters': [[32, 33], [34], [35, 36, 37]],
                'chapter_numbers': [12, 13, 14]
            },
            {
                'text': u'Disposizioni e documenti per l\'autotrasporto nazionale e internazionale',
                'chapters': [[38, 39, 40, 41, 42, 43], [44, 45, 46, 47]],
                'chapter_numbers': [15, 16]
            }
        ]
    },

    66: {
        'title': lazy_gettext('Revisioni CQC persone'),
        'exam_meta': {
            'max_errors': 4,
            'total_time': 2400,
            'num_questions': 40,
            'questions_per_chapter': [3, 2, 3, 2, 3, 2, 2, 2, 2, 3, 3, 3, 2, 3,
                                      3, 2]
        },
        'areas': [
            {
                'text': u'Segnaletica stradale e disposizioni per il conducente',
                'chapters': [[1], [2, 3], [4], [5, 6, 7, 8, 9]],
                'chapter_numbers': [1, 2, 3, 4]
            },
            {
                'text': u'Norme di comportamento sulla strada e consapevolezza ambientale',
                'chapters': [[10, 11, 12, 13, 14], [15, 16, 17], [18, 19], [20, 21, 22, 23, 24]],
                'chapter_numbers': [5, 6, 7, 8]
            },
            {
                'text': u'Condizioni psico-fisiche del conducente e visibilità nella guida',
                'chapters': [[25, 26, 27, 28], [29]],
                'chapter_numbers': [9, 10]
            },
            {
                'text': u'Normativa sociale nei trasporti professionali',
                'chapters': [[30, 31]],
                'chapter_numbers': [11]
            },
            {
                'text': u'Comportamenti per la sicurezza dei veicoli e del carico',
                'chapters': [[32, 33], [34], [35, 36, 37]],
                'chapter_numbers': [12, 13, 14]
            },
            {
                'text': u'Disposizioni e documenti per l\'autotrasporto nazionale e internazionale',
                'chapters': [[38, 39, 40], [41, 42]],
                'chapter_numbers': [15, 16]
            }
        ]
    }
}
