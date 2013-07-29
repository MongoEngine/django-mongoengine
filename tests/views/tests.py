# -*- coding: utf-8 -*-
from __future__ import absolute_import

import datetime
import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tests.settings")

from django import test
test.utils.setup_test_environment()

from django_mongoengine.tests import MongoTestCase

from .models import Artist, Author, Book, Page


class TestCase(MongoTestCase):

    def _fixture_setup(self):
        Artist.drop_collection()
        Author.drop_collection()
        Book.drop_collection()
        Page.drop_collection()

        Artist(id="1", name="Rene Magritte").save()

        Author(id="1", name=u"Roberto Bolaño", slug="roberto-bolano").save()
        scott = Author(id="2", name="Scott Rosenberg", slug="scott-rosenberg").save()

        Book(**{
            "id": "1",
            "name": "2066",
            "slug": "2066",
            "pages": "800",
            "authors": [scott],
            "pubdate": datetime.datetime(2008, 10, 01)
        }).save()

        Book(**{
            "id": "2",
            "name": "Dreaming in Code",
            "slug": "dreaming-in-code",
            "pages": "300",
            "pubdate": datetime.datetime(2006, 05, 01)
        }).save()

        Page(**{
            "id": "1",
            "template": "views/page_template.html",
            "content": "I was once bitten by a moose."
        }).save()


from .base import ViewTest, TemplateViewTest, RedirectViewTest
from .detail import DetailViewTest
from .edit import (FormMixinTests, ModelFormMixinTests, CreateViewTests,
    UpdateViewTests, DeleteViewTests)
from .list import ListViewTests
