
Quiz
----

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
      Content-Type: application/json

      {
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


   =========  ================================
   Question fields
   ===========================================
   id         question ID
   text       question text
   answer     question answer (True=1/False=0)
   image      image ID (optional)
   image_bis  image type (optional)
   =========  ================================


   :param topic_id: Topic for which questions are requested.

   :query lang: Question language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).


   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 400: Missing parameter: topic_id is missing.
   :statuscode 400: Invalid topic_id value.



.. http:post:: /quiz/(topic_id)

   Send quiz results for the specified topic.

   :form id: List of answered question IDs.
   :form answers: List of answers regarding to id list.
      Positive answer is 1 and negative is 0.

  
   :statuscode 200: Everything is ok.

   :statuscode 401: Unauthorized.
      Authentication is not passed.

   :statuscode 400: Missing parameter.
      At least one of the parameters is empty or missing.

   :statuscode 400: Parameters length mismatch.
      Lists has different numbers of elements.

   :statuscode 400: Invalid value.
      List element is not a number.
