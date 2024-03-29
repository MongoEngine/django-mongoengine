import logging

from bson import json_util
from django.conf import settings
from django.contrib.sessions.backends.base import CreateError, SessionBase
from django.core.exceptions import SuspiciousOperation
from django.utils import timezone
from django.utils.encoding import force_str
from mongoengine import fields
from mongoengine.connection import DEFAULT_CONNECTION_NAME
from mongoengine.document import Document
from mongoengine.queryset import OperationError

MONGOENGINE_SESSION_DB_ALIAS = getattr(
    settings, "MONGOENGINE_SESSION_DB_ALIAS", DEFAULT_CONNECTION_NAME
)

# a setting for the name of the collection used to store sessions
MONGOENGINE_SESSION_COLLECTION = getattr(
    settings, "MONGOENGINE_SESSION_COLLECTION", "django_session"
)

# a setting for whether session data is stored encoded or not
MONGOENGINE_SESSION_DATA_ENCODE = getattr(settings, "MONGOENGINE_SESSION_DATA_ENCODE", True)


class MongoSession(Document):
    session_key = fields.StringField(primary_key=True, max_length=40)
    session_data = fields.StringField() if MONGOENGINE_SESSION_DATA_ENCODE else fields.DictField()
    expire_date = fields.DateTimeField()

    meta = {
        "collection": MONGOENGINE_SESSION_COLLECTION,
        "db_alias": MONGOENGINE_SESSION_DB_ALIAS,
        "allow_inheritance": False,
        "indexes": [{"fields": ["expire_date"], "expireAfterSeconds": 0}],
    }

    def get_decoded(self):
        return SessionStore().decode(self.session_data)


class SessionStore(SessionBase):
    """A MongoEngine-based session store for Django."""

    def load(self):
        try:
            s = MongoSession.objects(session_key=self.session_key, expire_date__gt=timezone.now)[0]
            if MONGOENGINE_SESSION_DATA_ENCODE:
                return self.decode(force_str(s.session_data))
            else:
                return s.session_data
        except (IndexError, SuspiciousOperation) as e:
            if isinstance(e, SuspiciousOperation):
                logger = logging.getLogger("django.security.%s" % e.__class__.__name__)
                logger.warning(force_str(e))
            self._session_key = None
            return {}

    def exists(self, session_key):
        return bool(MongoSession.objects(session_key=session_key).first())

    def create(self):
        while True:
            self._session_key = self._get_new_session_key()
            try:
                self.save(must_create=True)
            except CreateError:
                continue
            self.modified = True
            return

    def save(self, must_create=False):
        if self.session_key is None:
            self.create()
        data = self._get_session(no_load=must_create)
        s = MongoSession(session_key=self.session_key)
        if MONGOENGINE_SESSION_DATA_ENCODE:
            s.session_data = self.encode(data)
        else:
            s.session_data = data
        s.expire_date = self.get_expiry_date()
        try:
            s.save(force_insert=must_create)
        except OperationError:
            if must_create:
                raise CreateError
            raise

    def delete(self, session_key=None):
        if session_key is None:
            if self.session_key is None:
                return
            session_key = self.session_key
        MongoSession.objects(session_key=session_key).delete()


class BSONSerializer:
    """
    Serializer that can handle BSON types (eg ObjectId).
    """

    def dumps(self, obj):
        return json_util.dumps(obj, separators=(",", ":")).encode("ascii")

    def loads(self, data):
        return json_util.loads(data.decode("ascii"))
