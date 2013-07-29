from django.test import TestCase
from django.conf import settings

from django_mongoengine import connect
from django_mongoengine import DEFAULT_CONNECTION_NAME

class MongoTestCase(TestCase):
    """
    TestCase class that clear the collection between the tests.
    """

    def __init__(self, methodName='runtest'):
        db_name = 'test_%s' % settings.MONGODB_DATABASES.get(
                DEFAULT_CONNECTION_NAME).get('name')
        self.conn = connect(db_name)
        super(MongoTestCase, self).__init__(methodName)

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        for collection in self.conn.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)

    def _fixture_setup(self):
        return

    def _fixture_teardown(self):
        return
