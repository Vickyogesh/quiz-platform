
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
      WWW-Authenticate: QuizAuth nonce="591261acf38824c458260f24db5cfe2c"

.. http:post:: /authorize

   Authorize.

   To authorize clinet send data in the *Authorization* header
   with the following parameters:

     * nonce - server nonce
     * appid - application ID
     * username - user login
     * digest - authorization digest

   Digest formula::

     HA1 = MD5(username:password)
     DIGEST = MD5(nonce:H1)

   After successful authorization the service creates a session and
   send response with the session ID in the cookie (*QUIZSID*).
   Client must use (and will by default) *QUIZSID* for future requests.

   **Example request**:

   .. sourcecode:: http

      POST /v1/authorize HTTP/1.1
      Authorization: QuizAuth nonce="591261acf38824c458260f24db5cfe2c",
                              appid="32bfe1c505d4a2a042bafd53993f10ece3ccddca",
                              username="chuck@norris.com",
                              digest="30926df486b100cfcb410193d26aaf34"

   **Example response**:

   .. sourcecode:: http

      HTTP/1.1 200 OK
      Set-cookie: QUIZSID="..."

   :statuscode 200: Authorization is passed.

   :statuscode 400: Invalid parameters:
      for example, client sent wrong application ID or digest is missing.

   :statuscode 400: Authorization is invalid:
      client sent wrong auth data.
