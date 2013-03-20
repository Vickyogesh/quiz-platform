Error Review
------------

Error review is a list of 40 random questions where student made a mistake
(in exam or quiz).

  =========  ================================
  Question fields
  ===========================================
  id         question ID
  text       question text
  answer     question answer (True=1/False=0)
  image      image ID (optional)
  image_bis  image type (optional)
  =========  ================================

.. http:get:: /errorreview

   Get error review questions.

   **Example requests**:

   .. sourcecode:: http

      GET /v1/errorreview HTTP/1.1

   .. sourcecode:: http

      GET /v1/errorreview?lang=fr HTTP/1.1


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "questions": [
          {
            "answer": 0,
            "text": "Question text1",
            "image": 234,
            "id": 12
          },
          {
            "answer": 1,
            "text": "Question text2",
            "image": 34,
            "id": 103,
            "image_bis": "b"
          },
          {
            "answer": 1,
            "text": "Question text3",
            "id": 208
          }
        ]
      }

   :query lang: Question language: *it*, *fr*, *de*.
     This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.


.. http:post:: /errorreview

   Send answers for the error review questions.
   List of questions is not fixed to 40.

   **Example request**:

   .. sourcecode:: http

      POST /v1/errorreview HTTP/1.1
      Content-Type: application/json; charset=utf-8

      {
        "questions": [1,2,3,10],
        "answers": [1,0,0,1]
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
      }

   =========  ==========================
   Request fields
   =====================================
   questions  List of answered questions
   answers    List of answers.

              *1* - Positive answer;
              *0* - Negative answer.

              *Number of answers must
              be the same as questions.*
   =========  ==========================

   :statuscode 200: Everything is ok.

   :statuscode 401: Unauthorized.

   :statuscode 400: Not a JSON.
      Client sent malformed JSON string.

   :statuscode 400: Missing parameter.
      At least one of the parameters missing.

   :statuscode 400: Parameters length mismatch.
      Lists has different numbers of elements.

   :statuscode 400: Invalid value.
      List element is not a number.
