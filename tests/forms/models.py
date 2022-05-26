from django.db import models

from django_mongoengine import Document, fields


class MongoDoc(Document):
    year = fields.IntField()
    file = fields.FileField(upload_to="test")


class DjangoModel(models.Model):
    year = models.IntegerField()
    file = models.FileField(upload_to="test")
