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
from django.test import SimpleTestCase, TestCase
from django.conf import settings

from mongoengine import connect
from mongoengine import DEFAULT_CONNECTION_NAME


class MongoTestCase(SimpleTestCase):
    """
    TestCase class that clear the collection between the tests.
    """
    assertQuerysetEqual = TestCase.__dict__['assertQuerysetEqual']

    def _pre_setup(self):
        super(MongoTestCase, self)._pre_setup()
        db_name = 'test_%s' % settings.MONGODB_DATABASES.get(
            DEFAULT_CONNECTION_NAME
        ).get('name')
        self.conn = connect(db_name)

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        for collection in self.conn.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)
