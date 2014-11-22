Student Statistics
------------------

Student statistics provides learning progress information of the student.

.. http:get:: /student

   **Access**: student, guest

   Get statistics for the current user. Same as :http:get:`/student/me`.
   
   .. seealso:: :http:get:`/student/(id)`


.. http:get:: /student/me

   **Access**: student, guest

   Get statistics for the current user. Same as :http:get:`/student`.
   
   .. seealso:: :http:get:`/student/(id)`


.. http:get:: /student/(id)

   **Access**: school, student, guest

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
        "exams": {
            "current": 10,
            "week": 80,
            "week3": 35
        },
        "topics": [
          {
            "id": 1,
            "text": "Topic 1",
            "errors": {
              "current": 12,
              "week": 34.5,
              "week3": -1
            }
          },
          {
            "id": 2,
            "text": "Topic 2",
            "errors": {
              "current": -1,
              "week": -1,
              "week3": -1
            }
          }
        ]
      }


   =========  ===========================================
   Response fields
   ======================================================
   student    Information about the student.
   exams      Exam statistics.
   topics     Statistics for each topic.
   =========  ===========================================

   =========  ===========================================
   student fields
   ======================================================
   id         Student ID.
   name       Student name.
   surname    Student surname.
   =========  ===========================================

   =========  ============================================
   exams fields
   =======================================================
   current    Current percent of failed exams.
   week       Last week percent of failed exams (average).
   week3      Average percent of failed exams in the range
              [3 weeks ago - week ago].
   =========  ============================================


   =========  =========================================
   topics fields
   ====================================================
   id         Topic ID.
   text       Topic text.
   errors     Information about errors for this topic.
              Percent of errors for this topic based
              on quizzes, exams and error reviews
              results.
   =========  =========================================

   =========  ==========================================
   errors fields
   =====================================================
   current    Current percent of errors.
   week       Last week percent of errors (average).
   week3      Average percent of errors in the range
              [3 weeks ago - week ago].

              **-1** value means  that there is no
              data for the given period.
   =========  ==========================================

   :param id: Student ID.

   :query lang: Topic text language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Unknown student - User with specified **id** is not present.
   :statuscode 400: Not a student - User with specified **id** is not a student.


.. http:get:: /student/(id)/exam

   **Access**: school, student, guest

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
        "exams": {
          "current": [
              {
                "id": 1,
                "start": "2013-03-29 07:12:11",
                "end": "2013-03-29 07:20:00",
                "errors": 5,
                "status": "failed"
              },
              {
                "id": 2,
                "start": "2013-03-29 07:25:11",
                "end": "None",
                "errors": 0,
                "status": "expired"
              },
              {
                "id": 3,
                "start": "2013-03-29 11:12:42",
                "end": "None",
                "errors": 0,
                "status": "in-progress"
              }
            ],
          "week": [   ],
          "week3": [   ]
        }
      }


   =========  ===========================================
   Response fields
   ======================================================
   student    Information about the student.
   exams      List of statistics for each exam.
   =========  ===========================================

   =========  ==========================================
   exams fields
   =====================================================
   id         Exam ID.
   start      Exam start date (UTC).
   end        Exam end date (UTC).
   errors     Number of wrong answers.
   status     Exam status. It may contain on the
              following value:

              * *'passed'* - exam is passed successfully
              * *'failed'* - exam is failed
              * *'expired'* - exam is expired
              * *'in-progress'* - exam is not passed yet
   =========  ==========================================

   :param id: Student ID.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Unknown student - User with specified **id** is not present.
   :statuscode 400: Not a student - User with specified **id** is not a student.


.. http:get:: /student/(id)/topicerrors/(topic_id)

   **Access**: school, student, guest

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
   :statuscode 403: Forbidden.
