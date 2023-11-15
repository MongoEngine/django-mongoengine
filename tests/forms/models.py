from django.db import models

from django_mongoengine import Document, fields


class MongoDoc(Document):
    year = fields.IntField(required=True)
    file = fields.FileField(upload_to="test", required=True)


class DjangoModel(models.Model):
    year = models.IntegerField()
    file = models.FileField(upload_to="test")
