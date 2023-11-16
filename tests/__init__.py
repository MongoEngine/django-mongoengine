from django.test import SimpleTestCase, TransactionTestCase
from mongoengine import connect
from mongoengine.connection import get_db

__all__ = ["MongoTestCase"]


class MongoTestCase(SimpleTestCase):
    """
    TestCase class that clear the collection between the tests
    """

    try:
        assertQuerySetEqual = TransactionTestCase.__dict__["assertQuerySetEqual"]
    except KeyError:
        # https://docs.djangoproject.com/en/4.2/topics/testing/tools/#django.test.TransactionTestCase.assertQuerySetEqual
        # Drop this after supporting only django > 4.2
        assertQuerySetEqual = TransactionTestCase.__dict__["assertQuerysetEqual"]

    def __init__(self, methodName="runtest"):
        from django.conf import settings

        connect(settings.MONGODB_DATABASES["default"]["name"])
        self.db = get_db()
        super().__init__(methodName)

    def dropCollections(self):
        for collection in self.db.list_collection_names():
            if collection.startswith("system."):
                continue
            self.db.drop_collection(collection)

    def tearDown(self):
        self.dropCollections()
