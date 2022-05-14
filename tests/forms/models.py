from django.db import models

from django_mongoengine import Document, fields


class MongoDoc(Document):
    intfield = fields.IntField()


class DjangoModel(models.Model):
    intfield = models.IntegerField()
