School
------

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
   :statuscode 400: Invalid parameters.
   :statuscode 400: Already exists.
        Student with the same login is already exists.
   :statuscode 400: Unknown school.
