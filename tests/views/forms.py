#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, division, print_function

from django_mongoengine import forms

from .models import Author


class AuthorForm(forms.DocumentForm):
    name = forms.CharField()
    slug = forms.SlugField()

    class Meta:
        document = Author
