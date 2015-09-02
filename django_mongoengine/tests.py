from django.test import SimpleTestCase
from django.conf import settings

from django_mongoengine import connect
from django_mongoengine import DEFAULT_CONNECTION_NAME

class MongoTestCase(SimpleTestCase):
    """
    TestCase class that clear the collection between the tests.
    """

    def _pre_setup(self):
        super(MongoTestCase, self)._pre_setup()
        db_name = 'test_%s' % settings.MONGODB_DATABASES.get(
                DEFAULT_CONNECTION_NAME).get('name')
        self.conn = connect(db_name)

    def _post_teardown(self):
        super(MongoTestCase, self)._post_teardown()
        for collection in self.conn.db.collection_names():
            if collection == 'system.indexes':
                continue
            self.db.drop_collection(collection)
