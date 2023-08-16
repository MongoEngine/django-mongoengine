#!/usr/bin/env python

from django import forms

from django_mongoengine.forms import DocumentForm

from .models import Author


class AuthorForm(DocumentForm):
    name = forms.CharField()
    slug = forms.SlugField()

    class Meta:
        document = Author
        fields = "__all__"
