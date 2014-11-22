Administration
--------------

.. http:get:: /admin/schools

   **Access**: admin

   Get list of registered schools.

   **Example request**:

   .. sourcecode:: http

      GET /admin/schools HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200,
        "schools": [
          {
            "id": 1,
            "name": "Chuck Norris School",
            "login": "chuck@norris.com"
          },
          {
            "id": 5,
            "name": "Rambo School",
            "login": "rambo@rambo.com"
          }
        ]
      }

   =========  ===========================================
   schools fields
   ======================================================
   id         School ID.
   name       School name.
   login      School login.
   =========  ===========================================

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.


.. http:post:: /admin/newschool

   **Access**: admin

   Create new school and guest student for this school.

   **Example request**:

   .. sourcecode:: http

      POST /admin/newschool HTTP/1.1
      Content-Type: application/json; charset=utf-8

      {
        "name": "Chuck Norris School",
        "login": "chuck@norris.com",
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
        "id": 42
      }

   Response contains created school *id*.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Missing parameter.
   :statuscode 400: Invalid parameters.
   :statuscode 400: Already exists.
        School with the same login is already exists.


.. http:delete:: /admin/school/(id)

   **Access**: admin

   Delete school.

   .. note:: All school's students and their data will be removed too.

   .. note:: You also may use :http:post:`/admin/school/(id)`.

   **Example request**:

   .. sourcecode:: http

      DELETE /admin/school/1 HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200
      }

   :param id: School ID.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Invalid school ID.


.. http:post:: /admin/school/(id)

   **Access**: admin

   Delete school.

   .. important:: You always have to provide *action=delete*
    as a query parameter.

   .. seealso:: :http:delete:`/admin/school/(id)`

   **Example request**:

   .. sourcecode:: http

      POST /admin/school/1?action=delete HTTP/1.1

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 200
      }

   :param id: School ID.

   :query action: Required parameter. Must be '*delete*'.

   :statuscode 200: Everything is ok.
   :statuscode 401: Unauthorized.
   :statuscode 403: Forbidden.
   :statuscode 400: Invalid action.
   :statuscode 400: Invalid request.
   :statuscode 400: Invalid school ID.



Guest account
^^^^^^^^^^^^^

Guest account will be created additionally to the school::

    login: [school_login]-guest
    password: guest

For example::

    school login: someschool@mail.com

    guest
    --------------------------------
    login: someschool@mail.com-guest
    password: guest
