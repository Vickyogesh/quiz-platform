
Authorization
-------------

Before call web service methods client must pass authorization.
At first, client send :http:get:`/authorize` request to get
authorization parameters. And then send :http:post:`/authorize`
with the user's authorization information.

.. http:get:: /authorize

   Request authorization parameters.

   The Service returns **nonce** which user have to use to build
   authorization data.

   **Example request**:

   .. sourcecode:: http

      GET /v1/authorize HTTP/1.1


   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8

      {
        "status": 401,
        "nonce": "cf7d8c2e4511132eb3acf7082e9147d9"
      }


.. http:post:: /authorize

   Authorize.

   To authorize clinet sends JSON with the following fields:

     * nonce - server nonce
     * appid - application ID
     * login - user login
     * digest - authorization digest

   Digest formula::

     HA1 = MD5(login:password)
     DIGEST = MD5(nonce:H1)

   After successful authorization the service creates a session and
   send response with the JSON which contains session ID in the filed *sid*
   and also in the cookie (*QUIZSID*).
   For cross-domain requests the client have to pass *sid* parameter
   in the URL for future requests, otherwise session ID will be passed
   in the cookie if possible.
   In the *user* field server sends information about authorized user.

   **Example request**:

   .. sourcecode:: http

      POST /v1/authorize HTTP/1.1
      Content-Type: application/json; charset=utf-8

      {
        "nonce": "cf7d8c2e4511132eb3acf7082e9147d9",
        "login": "testuser",
        "appid": "32bfe1c505d4a2a042bafd53993f10ece3ccddca",
        "digest": "2389ce38fd88cfcdce0484269cbbccb2"
      }

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Content-Type: application/json; charset=utf-8
      Set-Cookie: QUIZSID=964a2cb2afd34d2e9bc7c037a4c6d241

      {
        "status": 200,
        "sid": "964a2cb2afd34d2e9bc7c037a4c6d241",
        "user": {
          "id": 42,
          "name": "Chuck",
          "surname": "Norris",
          "type": "student"
        }
      }

   =========  =================================
   Response fields
   ============================================
   sid        Session ID.
   user       User metadata.
   =========  =================================

   =========  =================================
   user fields
   ============================================
   id         User ID.
   name       User name (or school name).
   surname    User surname. Only for students.
   type       User type: *student*, *school*,
              *guest*, *admin*.
   =========  =================================

   :statuscode 200: Authorization is passed.

   :statuscode 400: Invalid parameters:
      for example, client sent wrong application ID or digest is missing.

   :statuscode 400: Authorization is invalid:
      client sent wrong auth data.
