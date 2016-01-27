==================
Django-MongoEngine
==================

DO NOT CLONE UNTIL STABLE

Working
-------

* sessions
* models/fields
* auth? need testing

TODO
----

* Fix tests/
* Fix example app: example/tumblelog
* Sync some files/docs that removed from mongoengine: https://github.com/seglberg/mongoengine/commit/a34f4c1beb93f430c37da20c8fd96ce02a0f20c1?diff=unified
* Add docs for integrating: https://github.com/hmarr/django-debug-toolbar-mongo

Connecting
==========

In your **settings.py** file, add following lines::

    MONGODB_DATABASES = {
        "default": {
            "name": database_name,
            "host": database_host,
            "password": database_password,
            "username": database_user,
            "tz_aware": True, # if you using timezones in django (USE_TZ = True)
        },
    }


Sessions
========
Django allows the use of different backend stores for its sessions. MongoEngine
provides a MongoDB-based session backend for Django, which allows you to use
sessions in your Django application with just MongoDB. To enable the MongoEngine
session backend, ensure that your settings module has
``'django.contrib.sessions.middleware.SessionMiddleware'`` in the
``MIDDLEWARE_CLASSES`` field  and ``'django.contrib.sessions'`` in your
``INSTALLED_APPS``. From there, all you need to do is add the following line
into your settings module::

    SESSION_ENGINE = 'django_mongoengine.sessions'
    SESSION_SERIALIZER = 'django_mongoengine.sessions.BSONSerializer'

Django provides session cookie, which expires after
```SESSION_COOKIE_AGE``` seconds, but doesn't delete cookie at sessions
backend, so ``'mongoengine.django.sessions'`` supports  `mongodb TTL <http://docs.mongodb.org/manual/tutorial/expire-data/>`_.

.. note:: ``SESSION_SERIALIZER`` is only necessary in Django>1.6 as the default
   serializer is based around JSON and doesn't know how to convert
   ``bson.objectid.ObjectId`` instances to strings.


How to run example app
----------------------
.. code::

    virtualenv env
    ./env/bin/pip install .
    ./env/bin/pip install -r example/tumblelog/requirements.txt
    ./env/bin/python example/tumblelog/manage.py runserver
