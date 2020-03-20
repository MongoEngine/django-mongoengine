#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, division, print_function
import unittest

from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse
from django.views.generic.edit import FormMixin

from django_mongoengine import forms

from tests import MongoTestCase
from .models import Artist, Author
from .tests import TestCase

from . import views


class FormMixinTests(unittest.TestCase):
    def test_initial_data(self):
        """ Test instance independence of initial data dict (see #16138) """
        initial_1 = FormMixin().get_initial()
        initial_1['foo'] = 'bar'
        initial_2 = FormMixin().get_initial()
        self.assertNotEqual(initial_1, initial_2)


class CreateViewTests(MongoTestCase):

    def setUp(self):
        Author.drop_collection()

    def test_create(self):
        res = self.client.get('/edit/authors/create/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.context['form'], forms.DocumentForm))
        self.assertFalse('object' in res.context)
        self.assertFalse('author' in res.context)
        self.assertTemplateUsed(res, 'views/author_form.html')

        res = self.client.post('/edit/authors/create/',
                               {'id': 1,
                                'name': 'Randall Munroe',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe>'])

    def test_create_invalid(self):
        res = self.client.post('/edit/authors/create/',
                               {'id': 1,
                                'name': 'A' * 101,
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'views/author_form.html')
        self.assertEqual(len(res.context['form'].errors), 1)
        self.assertEqual(Author.objects.count(), 0)

    def test_create_with_object_url(self):
        res = self.client.post('/edit/artists/create/',
                               {'id': 1,
                                'name': 'Rene Magritte'})
        self.assertEqual(res.status_code, 302)
        artist = Artist.objects.get(name='Rene Magritte')
        self.assertRedirects(res, '/detail/artist/%s/' %
                             artist.pk)
        self.assertQuerysetEqual(Artist.objects.all(),
                                 ['<Artist: Rene Magritte>'])

    def test_create_with_redirect(self):
        res = self.client.post('/edit/authors/create/redirect/',
                               {'id': 1,
                                'name': 'Randall Munroe',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/edit/authors/create/')
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe>'])

    def test_create_with_interpolated_redirect(self):
        res = self.client.post('/edit/authors/create/interpolate_redirect/',
                               {'id': 1,
                                'name': 'Randall Munroe',
                                'slug': 'randall-munroe'})
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe>'])
        self.assertEqual(res.status_code, 302)
        pk = Author.objects.all()[0].pk
        self.assertRedirects(res, '/edit/author/%s/update/' %
                             pk)

    def test_create_with_special_properties(self):
        res = self.client.get('/edit/authors/create/special/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.context['form'], views.AuthorForm))
        self.assertFalse('object' in res.context)
        self.assertFalse('author' in res.context)
        self.assertTemplateUsed(res, 'views/form.html')

        res = self.client.post('/edit/authors/create/special/',
                               {'id': 1,
                                'name': 'Randall Munroe',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        obj = Author.objects.get(slug='randall-munroe')
        self.assertRedirects(res,
                             reverse('author_detail',
                                     kwargs={'pk': obj.pk}))
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe>'])

    def test_create_without_redirect(self):
        try:
            self.client.post('/edit/authors/create/naive/', {
                'id': 1,
                'name': 'Randall Munroe',
                'slug': 'randall-munroe'})
            self.fail(
                'Should raise exception -- No redirect URL provided, and no get_absolute_url provided')
        except ImproperlyConfigured:
            pass


class UpdateViewTests(TestCase):

    def setUp(self):
        Author.drop_collection()

    def test_update_post(self):
        a = Author.objects.create(id='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.get('/edit/author/%s/update/' % a.pk)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.context['form'], forms.DocumentForm))
        self.assertEqual(res.context['object'], Author.objects.get(pk=a.pk))
        self.assertEqual(res.context['author'], Author.objects.get(pk=a.pk))
        self.assertTemplateUsed(res, 'views/author_form.html')

        # Modification with both POST and PUT (browser compatible)
        res = self.client.post('/edit/author/%s/update/' % a.pk,
                               {'id': '1',
                                'name': 'Randall Munroe (xkcd)',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe (xkcd)>'])

    @unittest.expectedFailure
    def test_update_put(self):
        a = Author.objects.create(id='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.get('/edit/author/%s/update/' % a.pk)
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'views/author_form.html')

        res = self.client.put('/edit/author/%s/update/' % a.pk,
                              {'name': 'Randall Munroe (author of xkcd)',
                               'slug': 'randall-munroe'})
        # Here is the expected failure. PUT data are not processed in any special
        # way by django. So the request will equal to a POST without data, hence
        # the form will be invalid and redisplayed with errors (status code 200).
        # See also #12635
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe (author of xkcd)>'])

    def test_update_invalid(self):
        a = Author.objects.create(id='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.post('/edit/author/%s/update/' % a.pk,
                               {'id': '1',
                                'name': 'A' * 101,
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 200)
        self.assertTemplateUsed(res, 'views/author_form.html')
        self.assertEqual(len(res.context['form'].errors), 1)
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe>'])

    def test_update_with_object_url(self):
        a = Artist.objects.create(id='1', name='Rene Magritte')
        res = self.client.post('/edit/artists/%s/update/' % a.pk,
                               {'id': '1',
                                'name': 'Rene Magritte'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/detail/artist/%s/' % a.pk)
        self.assertQuerysetEqual(Artist.objects.all(),
                                 ['<Artist: Rene Magritte>'])

    def test_update_with_redirect(self):
        a = Author.objects.create(id='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.post('/edit/author/%s/update/redirect/' % a.pk,
                               {'id': '1',
                                'name': 'Randall Munroe (author of xkcd)',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/edit/authors/create/')
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe (author of xkcd)>'])

    def test_update_with_interpolated_redirect(self):
        a = Author.objects.create(id='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.post('/edit/author/%s/update/interpolate_redirect/' %
                               a.pk,
                               {'id': '1',
                                'name': 'Randall Munroe (author of xkcd)',
                                'slug': 'randall-munroe'})
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe (author of xkcd)>'])
        self.assertEqual(res.status_code, 302)
        pk = Author.objects.all()[0].pk
        self.assertRedirects(res, '/edit/author/%s/update/' %
                             pk)

    def test_update_with_special_properties(self):
        a = Author.objects.create(id='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.get('/edit/author/%s/update/special/' % a.pk)
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.context['form'], views.AuthorForm))
        self.assertEqual(res.context['object'], Author.objects.get(pk=a.pk))
        self.assertEqual(res.context['thingy'], Author.objects.get(pk=a.pk))
        self.assertFalse('author' in res.context)
        self.assertTemplateUsed(res, 'views/form.html')

        res = self.client.post('/edit/author/%s/update/special/' % a.pk,
                               {'id': '1',
                                'name': 'Randall Munroe (author of xkcd)',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/detail/author/%s/' % a.pk)
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe (author of xkcd)>'])

    def test_update_without_redirect(self):
        with self.assertRaises(ImproperlyConfigured):
            a = Author.objects.create(id='1',
                                      name='Randall Munroe',
                                      slug='randall-munroe', )
            self.client.post('/edit/author/%s/update/naive/' % a.pk, {
                'id': '1',
                'name': 'Randall Munroe (author of xkcd)',
                'slug': 'randall-munroe'})

    def test_update_get_object(self):
        a = Author.objects.create(pk='1',
                                  name='Randall Munroe',
                                  slug='randall-munroe', )
        res = self.client.get('/edit/author/update/')
        self.assertEqual(res.status_code, 200)
        self.assertTrue(isinstance(res.context['form'], forms.DocumentForm))
        self.assertEqual(res.context['object'], Author.objects.get(pk=a.pk))
        self.assertEqual(res.context['author'], Author.objects.get(pk=a.pk))
        self.assertTemplateUsed(res, 'views/author_form.html')

        # Modification with both POST and PUT (browser compatible)
        res = self.client.post('/edit/author/update/',
                               {'id': '1',
                                'name': 'Randall Munroe (xkcd)',
                                'slug': 'randall-munroe'})
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(),
                                 ['<Author: Randall Munroe (xkcd)>'])


class DeleteViewTests(MongoTestCase):

    def setUp(self):
        Author.drop_collection()

    def test_delete_by_post(self):
        a = Author.objects.create(**{'id': '1',
                                     'name': 'Randall Munroe',
                                     'slug': 'randall-munroe'})
        res = self.client.get('/edit/author/%s/delete/' % a.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['object'], Author.objects.get(pk=a.pk))
        self.assertEqual(res.context['author'], Author.objects.get(pk=a.pk))
        self.assertTemplateUsed(res, 'views/author_confirm_delete.html')

        # Deletion with POST
        res = self.client.post('/edit/author/%s/delete/' % a.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(), [])

    def test_delete_by_delete(self):
        # Deletion with browser compatible DELETE method
        a = Author.objects.create(**{'id': '1',
                                     'name': 'Randall Munroe',
                                     'slug': 'randall-munroe'})
        res = self.client.delete('/edit/author/%s/delete/' % a.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(), [])

    def test_delete_with_redirect(self):
        a = Author.objects.create(**{'id': '1',
                                     'name': 'Randall Munroe',
                                     'slug': 'randall-munroe'})
        res = self.client.post('/edit/author/%s/delete/redirect/' % a.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/edit/authors/create/')
        self.assertQuerysetEqual(Author.objects.all(), [])

    def test_delete_with_special_properties(self):
        a = Author.objects.create(**{'id': '1',
                                     'name': 'Randall Munroe',
                                     'slug': 'randall-munroe'})
        res = self.client.get('/edit/author/%s/delete/special/' % a.pk)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.context['object'], Author.objects.get(pk=a.pk))
        self.assertEqual(res.context['thingy'], Author.objects.get(pk=a.pk))
        self.assertFalse('author' in res.context)
        self.assertTemplateUsed(res, 'views/confirm_delete.html')

        res = self.client.post('/edit/author/%s/delete/special/' % a.pk)
        self.assertEqual(res.status_code, 302)
        self.assertRedirects(res, '/list/authors/')
        self.assertQuerysetEqual(Author.objects.all(), [])

    def test_delete_without_redirect(self):
        try:
            a = Author.objects.create(id='1',
                                      name='Randall Munroe',
                                      slug='randall-munroe', )
            self.client.post('/edit/author/%s/delete/naive/' % a.pk)
            self.fail(
                'Should raise exception -- No redirect URL provided, and no get_absolute_url provided')
        except ImproperlyConfigured:
            pass
