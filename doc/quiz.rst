
Quiz
----

Quiz is a list of 40 random questions for the specified topic.

  =========  =================================
  Question fields
  ============================================
  id         Question ID.
  text       Question text.
  answer     Question answer (True=1/False=0).
  image      Image ID (optional).
  image_bis  Image type (optional).
  =========  =================================


.. http:get:: /quiz/(topic_id)

   Get quiz for the specified topic and language (optional).

   **Example requests**:

   .. sourcecode:: http

      GET /v1/quiz/1 HTTP/1.1

   .. sourcecode:: http

      GET /v1/quiz/42?lang=de HTTP/1.1


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "topic": 1,
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
            "id": 3,
            "image_bis": "b"
          },
          {
            "answer": 1,
            "text": "Question text3",
            "id": 108
          }
        ]
      }

   =========  ======================================
   Response fields
   =================================================
   topic      Quiz topic id
   questions  List of quiz questions
   =========  ======================================

   :param topic_id: Topic for which questions are requested.

   :query lang: Question language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 400: Invalid topic ID (temprorary removed - need to update quiz
    algo).


.. http:post:: /quiz/(topic_id)

   Send quiz results for the specified topic. Client sends list of answered
   questions and answers. List of questions is not fixed to 40.

   **Example request**:

   .. sourcecode:: http

      POST /v1/quiz/1 HTTP/1.1
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
        "status": 200
      }

   =========  ===========================
   Request fields
   ======================================
   questions  List of answered questions.
   answers    List of answers.

              *1* - Positive answer;
              *0* - Negative answer.

              *Number of answers must
              be the same as questions.*
   =========  ===========================

   :param topic_id: Topic of the quiz.


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
