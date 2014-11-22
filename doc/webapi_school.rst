School
------

.. http:get:: /school/(id)/students

   **Access**: school, admin

   Get list of students for the given school. If **id** is *me* then
   school id will be retrieved from the session on the server side.

   **Example requests**:

   .. sourcecode:: http

      GET /school/me/students HTTP/1.1

   .. sourcecode:: http

      GET /school/1/students HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "students": [
          {
            "id": 2,
            "name": "Chuck Norris School",
            "surname": "",
            "login": "chuck@norris.com-guest",
            "type": "guest",
          },
          {
            "id": 2,
            "name": "Chucky",
            "surname": "Norrisy",
            "login": "chucky@norrisy.com",
            "type": "student",
          }
        ]
      }

   =========  ===========================================
   students fields
   ======================================================
   id         Student ID.
   name       Student name.
   surname    Student surname.
   login      Student login.
   type       User type: *guest* or *student*.
   =========  ===========================================

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Invalid school ID.


.. http:post:: /school/(id)/newstudent

   **Access**: school

   Create new student for the given school. If **id** is *me* then
   school id will be retrieved from the session on the server side.

   **Example requests**:

   .. sourcecode:: http

      POST /school/12/newstudent HTTP/1.1
      Content-Type: application/json; charset=utf-8

      {
        "name": "Chuck Norris",
        "surname": "Son",
        "login": "chuck.jr@norris.com",
        "passwd": "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
      }

   .. sourcecode:: http

      POST /school/me/newstudent HTTP/1.1
      Content-Type: application/json; charset=utf-8

      {
        "name": "Chuck Norris",
        "surname": "Son",
        "login": "chuck.jr@norris.com",
        "passwd": "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
      }

   passwd formula::

     passwd = MD5(login:password)


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "id": 42,
        "name": "Chuck Norris",
        "surname": "Son"
      }

   Response contains info about created user.

   :param id: School ID.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Missing parameter.
   :statuscode 400: Invalid parameters.
   :statuscode 400: Already exists.
        Student with the same login is already exists.
   :statuscode 400: Invalid school ID.


.. http:delete:: /school/(id)/student/(student)

   **Access**: school

   Delete specified student from the given school. If **id** is *me* then
   school id will be retrieved from the session on the server side.

   .. note:: All student's data will be removed too.

   .. note:: You also may use :http:post:`/school/(id)/student/(student)`.

   **Example requests**:

   .. sourcecode:: http

      DELETE /school/me/student/10 HTTP/1.1

   .. sourcecode:: http

      DELETE /school/1/student/10 HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200
      }

   :param id: School ID.
   :param student: Student ID.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Invalid school ID.
   :statuscode 400: Unknown student.


.. http:post:: /school/(id)/student/(student)

   **Access**: school

   Delete specified student from the given school. If **id** is *me* then
   school id will be retrieved from the session on the server side.

   .. important:: You always have to provide *action=delete*
    as a query parameter.

   .. seealso:: :http:delete:`/school/(id)/student/(student)`

   **Example requests**:

   .. sourcecode:: http

      POST /school/me/student/10?action=delete HTTP/1.1

   .. sourcecode:: http

      POST /school/1/student/10?action=delete HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200
      }

   :param id: School ID.
   :param student: Student ID.

   :query action: Required parameter. Must be '*delete*'.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Invalid school ID.
   :statuscode 400: Unknown student.
   :statuscode 400: Invalid action.
   :statuscode 400: Invalid request.


.. http:get:: /school/(id)

   **Access**: school, admin

   Get statistics for the given school. If **id** is *me* then
   school id will be retrieved from the session on the server side.

   **Example request**:

   .. sourcecode:: http

      GET /v1/school/1 HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "guest_visits": [30,20,-1],
        "exams": [4,20,33],
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
        ],
        "students": {
          "current": {
            "worst": [
              {
                "id": 1,
                "name": "Chuck",
                "surname": "Norris",
                "coef": 0.45
              },
              {
                "id": 2,
                "name": "Chuck1",
                "surname": "Norris1",
                "coef": 0.5
              }
            ],
            "best": [
              {
                "id": 1,
                "name": "Chuck",
                "surname": "Norris",
                "coef": 0.45
              },
              {
                "id": 2,
                "name": "Chuck1",
                "surname": "Norris1",
                "coef": 0.5
              }
            ]
          },
          "week": {
            "worst": [
              {
                "id": 1,
                "name": "Chuck",
                "surname": "Norris",
                "coef": 0.45
              },
              {
                "id": 2,
                "name": "Chuck1",
                "surname": "Norris1",
                "coef": 0.5
              }
            ],
            "best": [
              {
                "id": 1,
                "name": "Chuck",
                "surname": "Norris",
                "coef": 0.45
              },
              {
                "id": 2,
                "name": "Chuck1",
                "surname": "Norris1",
                "coef": 0.5
              }
            ]
          },
          "week3": {
            "worst": [
              {
                "id": 1,
                "name": "Chuck",
                "surname": "Norris",
                "coef": 0.45
              },
              {
                "id": 2,
                "name": "Chuck1",
                "surname": "Norris1",
                "coef": 0.5
              }
            ],
            "best": [
              {
                "id": 1,
                "name": "Chuck",
                "surname": "Norris",
                "coef": 0.45
              },
              {
                "id": 2,
                "name": "Chuck1",
                "surname": "Norris1",
                "coef": 0.5
              }
            ]
          }

        }
      }

   ============   ====================================================
   Response fields
   ===================================================================
   guest_visits   List of guest visits (current, week, week3).
   exams          List of exams error percents (current, week, week3).
   topics         Statistics for each topic.
   students       Students rating.
   ============   ====================================================

   =========  =========================================
   topics fields
   ====================================================
   id         Topic ID.
   text       Topic text.
   errors     Information about errors for this topic.
              Percent of errors for this topic based
              on school's students activity.
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


   =========  =========================================
   students fields
   ====================================================
   current    Current rating.
   week       Week rating.
   week3      [3 weeks ago - week ago] rating.
   =========  =========================================

   =========  =========================================
   rating fields (current, week, week3)
   ====================================================
   best       Best students.
   worst      Worst students.
   =========  =========================================

   .. note:: **best** and **worst** fields may contain from zero to three items.


   :param id: School ID.

   :query lang: Topics language: *it*, *fr*, *de*.
      This parameter is optional (default: *it*).
