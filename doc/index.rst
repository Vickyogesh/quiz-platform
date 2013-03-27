Quiz Web Service API v1
===============================================

| This document describes API v1 of the Quiz Web Service (The Service).
| The following API is provided:

.. toctree::
   :titlesonly:

   auth
   quiz
   exam
   error_review
   student_stat
   admin
   school


General Information
-------------------

Data exchanging between the Service and the client is done using JSON format.
All Service errors is returned in JSON too. Each Service response contains
**status** field with HTTP status code:

.. sourcecode:: http
   
   HTTP/1.1 200 OK
   Content-Type: application/json; charset=utf-8

   {
      "status": 200
   }

Server error contains two fields: **status** and **description**:

.. sourcecode:: http

   HTTP/1.1 200 OK
   Content-Type: application/json; charset=utf-8

   {
      "status": 401,
      "description": "Unauthorized."
   }

.. note:: *Content-Type* HTTP header is assumed as *"application/json; charset=utf-8"*
    if not specified.


Cross-domain communication and sessions
---------------------------------------

The Service supports *Cross-Origin Resource Sharing* that allows
cross-domain communication from the client
(`CORS tutorial <http://www.html5rocks.com/en/tutorials/cors>`_).

The Service allows cross-domain requests from any server and because of this
feature client will not able to use cookies
(`MDN <https://developer.mozilla.org/en-US/docs/HTTP/Access_control_CORS#Requests_with_credentials>`_).
Thus client have to send session ID in the URL query parameter *sid*.
Note what you don't need to pass session ID if you do not use
cross-domain communication - cookies will be used by default.

*sid* parameter has higher priority if you send session in cookie
and in URL parameter.

To perform cross-domain request client have to get *sid* from the server
using authorization process and then append *sid=...* to all future
requests to the Service:

.. sourcecode:: http

   GET /v1/quiz/1?sid=28290aeebe674ccc8561f1ac1cd58e9e HTTP/1.1
   Content-Type: application/json; charset=utf-8

.. note:: *sid* parameter is skipped in the API documentation, but you have to
    pass it for all cross-domain requests.

See :doc:`auth` for more info.
