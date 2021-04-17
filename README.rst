==================
Django-MongoEngine
==================

|lifecycle| |gitter|

.. |lifecycle| image:: https://img.shields.io/osslifecycle/MongoEngine/django-mongoengine
   :alt: OSS Lifecycle

.. |gitter| image:: https://badges.gitter.im/gitterHQ/gitter.png
   :target: https://gitter.im/MongoEngine/django-mongoengine
   :alt: Gitter chat


THIS IS UNSTABLE PROJECT, IF YOU WANT TO USE IT - FIX WHAT YOU NEED

Right now we're targeting to get things working on Django 2.0 and 3.0;

WARNING:
--------
Maybe there is better option for mongo support, take a look at https://nesdis.github.io/djongo/;
It's python3 only and i have not tried it yet, but looks promising.


Working / Django 2.0-3.0
---------------------

* [ok] sessions
* [ok] models/fields, fields needs testing
* [ok] views
* [ok] auth
* [?] admin - partially working, some things broken

Current status
-------------------------------------------------------------------------------

Many parts of projects rewritten/removed;
Instead of copying django code i try to subclass/reuse/even monkey-patch;
Everything listed above is working; admin - just base fuctions
like changelist/edit, not tested with every form type; need's more work.

Some code just plaholder to make things work;
`django/forms/document_options.py` - dirty hack absolutely required to
get thigs work with django. It replaces mongo _meta on model/class and
provide django-like interface.
It get's replaced after class creation via some metaclass magick.

Fields notes
------------

* mongo defaults Field(required=False), changed to django-style defaults
  -> Field(blank=False), and setting required = not blank in Field.__init__



TODO
----

* Sync some files/docs that removed from mongoengine: https://github.com/seglberg/mongoengine/commit/a34f4c1beb93f430c37da20c8fd96ce02a0f20c1?diff=unified
* Add docs for integrating: https://github.com/hmarr/django-debug-toolbar-mongo
* Take a look at django-mongotools: https://github.com/wpjunior/django-mongotools

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

    INSTALLED_APPS += ["django_mongoengine"]

Documents
=========
Inhherit your documents from ``django_mongoengine.Document``,
and define fields using ``django_mongoengine.fields``.::

    from django_mongoengine import Document, EmbeddedDocument, fields

    class Comment(EmbeddedDocument):
        created_at = fields.DateTimeField(
            default=datetime.datetime.now, editable=False,
        )
        author = fields.StringField(verbose_name="Name", max_length=255)
        email  = fields.EmailField(verbose_name="Email")
        body = fields.StringField(verbose_name="Comment")

    class Post(Document):
        created_at = fields.DateTimeField(
            default=datetime.datetime.now, editable=False,
        )
        title = fields.StringField(max_length=255)
        slug = fields.StringField(max_length=255, primary_key=True)
        comments = fields.ListField(
            fields.EmbeddedDocumentField('Comment'), blank=True,
        )


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

    poetry install
    poetry run pip install -r example/tumblelog/requirements.txt
    poetry run python example/tumblelog/manage.py runserver


How to run tests
----------------
.. code::

    poetry install
    poetry run python -m pytest
