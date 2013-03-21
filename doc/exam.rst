Exam
----

Exam is a list of 40 random questions from all available topics.

.. http:get:: /exam

   Get exam for the user.
   The exam will expire after **3 hrs** since creation.

   **Example requests**:

   .. sourcecode:: http

      GET /v1/exam HTTP/1.1

   .. sourcecode:: http

      GET /v1/exam?lang=de HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "exam": {
          "id": 9,
          "expires": "2013-03-14 18:11:21"
        },
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

   =========  ===========================================
   Response fields
   ======================================================
   exam       Exam information.
   questions  List of exam questions.
   =========  ===========================================

   =========  ===========================================
   exam fields
   ======================================================
   id         Exam ID.
   expires    Expiration time of the exam (time in UTC).
              After this time the Service will not accept
              exam answers.
   =========  ===========================================

   =========  =================================
   question fields
   ============================================
   id         Question ID.
   text       Question text.
   answer     Question answer (True=1/False=0).
   image      Image ID (optional).
   image_bis  Image type (optional).
   =========  =================================

   :query lang: Question language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.


.. http:post:: /exam/(id)

   Send answers for the specified exam. Client sends list of answered
   questions and answers. List of questions/answers is fixed to 40.

   **Example request**:

   .. sourcecode:: http

      POST /v1/exam/9 HTTP/1.1
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

   :param id: ID of the exam.


   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 400: Not a JSON.
      Client sent malformed JSON string.
   :statuscode 400: Missing parameter.
      At least one of the parameters missing.
   :statuscode 400: Parameters length mismatch.
      Lists has different numbers of elements.
   :statuscode 400: Wrong number of answers.
        There must be 40 answers.
   :statuscode 400: Invalid exam ID.
   :statuscode 400: Invalid value.
      List element is not a number.
   :statuscode 400: Exam is already passed.
   :statuscode 400: Exam is expired.
   :statuscode 400: Invalid question ID.


.. http:get:: /exam/(id)

   Get information about specified exam.

   **Example requests**:

   .. sourcecode:: http

      GET /v1/exam/9 HTTP/1.1

   .. sourcecode:: http

      GET /v1/exam/9?lang=fr HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "student": {
          "id": 42,
          "name": "Chuck",
          "surname": "Norris"
        },
        "exam": {
          "id": 1,
          "start": "2013-03-19 17:16:00",
          "end": "2013-03-19 17:16:00",
          "errors": 2,
          "status": "passed"
        },
        "questions": [
          {
            "answer": 1,
            "text": "Question text2",
            "image": 34,
            "id": 3,
            "image_bis": "b",
            "is_correct": 1
          },
          {
            "answer": 2,
            "text": "Question text",
            "id": 90,
            "is_correct": 0
          }
        ]
      }

   =========  =============================
   Request fields
   ========================================
   student    Information about the student
              for whom exam was created.
   exam       Exam information.
   questions  List of exam questions.
   =========  =============================

   =========  ==================
   student fields
   =============================
   id         Student ID.
   name       Student name.
   surname    Student surname.
   =========  ==================

   =========  ============================================================
   exam fields
   =======================================================================
   id         Exam ID.
   start      Exam start time (UTC).
   end        Exam end time (UTC).
   errors     Number of errors.
   status     Exam status:

              * passed - exam is successfully passed
              * failed - exam is failed (number of errors > 4)
              * expired - exam is expired (it took more than 3 hours
                after exam creation).
              * in-progress - exams is in progress.
   =========  ============================================================

   ==========  =================================
   questions fields
   =============================================
   id          Question ID.
   text        Question text.
   answer      Question answer (True=1/False=0).
   image       Image ID (optional).
   image_bis   Image type (optional).
   is_correct  Correct answer (True=1/False=0).
   ==========  =================================


   :param id: ID of the exam.

   :query lang: Question language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 400: Invalid exam ID.

