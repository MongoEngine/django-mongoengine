from django.test import SimpleTestCase, TransactionTestCase

from mongoengine import connect
from mongoengine.connection import get_db

__all__ = ["MongoTestCase"]


class MongoTestCase(SimpleTestCase):
    """
    TestCase class that clear the collection between the tests
    """
    assertQuerysetEqual = TransactionTestCase.__dict__['assertQuerysetEqual']

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
