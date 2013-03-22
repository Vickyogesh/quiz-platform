Student Statistics
------------------

Student statistics provides learning progress information of the student.

.. http:get:: /student

   Get statistics for the current user. Same as :http:get:`/student/me`.
   
   .. seealso:: :http:get:`/student/(id)`


.. http:get:: /student/me

   Get statistics for the current user. Same as :http:get:`/student`.
   
   .. seealso:: :http:get:`/student/(id)`


.. http:get:: /student/(id)

   Get statistics for the student with specified ID.
   If **id** is *me* then current user id is used.

   **Example requests**:

   .. sourcecode:: http

      GET /v1/student/1 HTTP/1.1

   .. sourcecode:: http

      GET /v1/student/me HTTP/1.1

   .. sourcecode:: http

      GET /v1/student/42?lang=de HTTP/1.1


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
        "exams": [
          {
            "id": 1,
            "status": 5
          },
          {
            "id": 2,
            "status": "expired"
          },
          {
            "id": 3,
            "status": 0
          },
          {
            "id": 4,
            "status": "in-progress"
          }
        ],
        "topics": [
          {
            "id": 1,
            "text": "Topic 1",
            "errors": 20
          },
          {
            "id": 2,
            "text": "Topic 2",
            "errors": -1
          }
        ]
      }


   =========  ===========================================
   Response fields
   ======================================================
   student    Information about the student.
   exams      List of statistics for each exam.
   topics     List of statistics for each topic.
   =========  ===========================================

   =========  ===========================================
   student fields
   ======================================================
   id         Student ID.
   name       Student name.
   surname    Student surname.
   =========  ===========================================

   =========  ==========================================
   exams fields
   =====================================================
   id         Exam ID.
   status     Exam status. It may contain on the
              following value:

              * *number* - number of errors
              * *'expired'* - exam is expired 
              * *'in-progress'* - exam is not passed yet
   =========  ==========================================


   =========  ======================================
   topics fields
   =================================================
   id         Topic ID.
   text       Topic text.
   errors     Percent of errors for this topic based
              on quizzes, exams and error reviews
              results.

              **-1** value means
              that the student did not answer the
              questions in this topic.
   =========  ======================================

   :param id: Student ID.

   :query lang: Topic text language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 400: Unknown student - User with specified **id** is not present.
   :statuscode 400: Not a student - User with specified **id** is not a student.


.. http:get:: /student/(id)/exam

   Get exam list for the student with specified ID.
   If **id** is *me* then current user id is used.

   **Example requests**:

   .. sourcecode:: http

      GET /v1/student/1 HTTP/1.1

   .. sourcecode:: http

      GET /v1/student/me HTTP/1.1


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
        "exams": [
          {
            "id": 1,
            "status": 5
          },
          {
            "id": 2,
            "status": "expired"
          },
          {
            "id": 3,
            "status": 0
          },
          {
            "id": 4,
            "status": "in-progress"
          }
        ],
        "topics": [
          {
            "id": 1,
            "text": "Topic 1",
            "errors": 20
          },
          {
            "id": 2,
            "text": "Topic 2",
            "errors": -1
          }
        ]
      }


   =========  ===========================================
   Response fields
   ======================================================
   student    Information about the student.
   exams      List of statistics for each exam.
   topics     List of statistics for each topic.
   =========  ===========================================

   =========  ===========================================
   student fields
   ======================================================
   id         Student ID.
   name       Student name.
   surname    Student surname.
   =========  ===========================================

   =========  ==========================================
   exams fields
   =====================================================
   id         Exam ID.
   status     Exam status. It may contain on the
              following value:

              * *number* - number of errors
              * *'expired'* - exam is expired 
              * *'in-progress'* - exam is not passed yet
   =========  ==========================================


   =========  ======================================
   topics fields
   =================================================
   id         Topic ID.
   text       Topic text.
   errors     Percent of errors for this topic based
              on quizzes, exams and error reviews
              results.

              **-1** value means
              that the student did not answer the
              questions in this topic.
   =========  ======================================

   :param id: Student ID.

   :query lang: Topic text language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 400: Unknown student - User with specified **id** is not present.
   :statuscode 400: Not a student - User with specified **id** is not a student.


.. http:get:: /student/(id)/topicerrors/(topic_id)

   Get questions with wrong answers for the specified topic.

   **Example requests**:

   .. sourcecode:: http

      GET /v1/student/me/topicerrors/12 HTTP/1.1

   .. sourcecode:: http

      GET /v1/student/12/topicerrors/1?lang=fr HTTP/1.1


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
   student    Student info.
   questions  List of questions with wrong answers.
   =========  ======================================

   =========  ===========================================
   student fields
   ======================================================
   id         Student ID.
   name       Student name.
   surname    Student surname.
   =========  ===========================================

   =========  =================================
   questions fields
   ============================================
   id         Question ID.
   text       Question text.
   answer     Question answer (True=1/False=0).
   image      Image ID (optional).
   image_bis  Image type (optional).
   =========  =================================

   :param id: Student ID.
   :param topic_id: Topic ID for which questions are requested.

   :query lang: Question language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
