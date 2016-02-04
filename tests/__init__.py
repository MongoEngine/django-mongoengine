#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, division, print_function

import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

from django import test
test.utils.setup_test_environment()
try:
    import django
    django.setup()
except AttributeError:
    pass

from mongoengine import connect
from mongoengine.connection import get_db


class MongoTestCase(test.SimpleTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    assertQuerysetEqual = test.TransactionTestCase.__dict__['assertQuerysetEqual']

    def __init__(self, methodName='runtest'):
        from django.conf import settings
        connect(settings.MONGODB_DATABASES['default']['name'])
        self.db = get_db()
        super(MongoTestCase, self).__init__(methodName)

    def dropCollections(self):
        for collection in self.db.collection_names():
            if collection.startswith('system.'):
                continue
            self.db.drop_collection(collection)

    def tearDown(self):
        self.dropCollections()
