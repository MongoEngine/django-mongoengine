#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, division, print_function

import datetime

from tests import MongoTestCase

from .models import Artist, Author, Book, Page


class TestCase(MongoTestCase):

    def setUp(self):
        Artist.drop_collection()
        Author.drop_collection()
        Book.drop_collection()
        Page.drop_collection()

        Artist(id="1", name="Rene Magritte").save()

        Author(id="1", name=u"Roberto Bolaño", slug="roberto-bolano").save()
        scott = Author(id="2",
                       name="Scott Rosenberg",
                       slug="scott-rosenberg").save()

        Book(**{
            "id": "1",
            "name": "2066",
            "slug": "2066",
            "pages": "800",
            "authors": [scott],
            "pubdate": datetime.datetime(2008, 10, 1)
        }).save()

        Book(**{
            "id": "2",
            "name": "Dreaming in Code",
            "slug": "dreaming-in-code",
            "pages": "300",
            "authors": [scott],
            "pubdate": datetime.datetime(2006, 5, 1)
        }).save()

        Page(**{
            "id": "1",
            "template": "views/page_template.html",
            "content": "I was once bitten by a moose."
        }).save()


from .detail import * # noqa
from .edit import *   # noqa
from .list import *   # noqa
