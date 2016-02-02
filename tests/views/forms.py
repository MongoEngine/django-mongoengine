#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, division, print_function

from django import forms
from django_mongoengine.forms import DocumentForm

from .models import Author


class AuthorForm(DocumentForm):
    name = forms.CharField()
    slug = forms.SlugField()

    class Meta:
        document = Author
        fields = "__all__"
