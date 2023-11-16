=========
Examples
=========

Embedded Fields
===============
**models.py**::

    from django.db import models
    from django_mongoengine import Document, EmbeddedDocument, fields

    class Product(Document):
        name = fields.StringField()
        retail_price = fields.DecimalField(
            max_digits=15, decimal_places=2, default=0)
        inventory_price = fields.DecimalField(
            max_digits=15, decimal_places=2, default=0)

    class ContactInfo(EmbeddedDocument):
        web = fields.URLField(help_text=_("""List of languages for your application (the first one will be the default language)"""))
        email = fields.EmailField(verbose_name=_('e-mail address'))
        phone = fields.StringField(verbose_name=_('phone number'))

    class Application(Document):
        name = fields.StringField(max_length=255, required=True)
        contact = fields.EmbeddedDocumentField(ContactInfo)
        LOCALES = (('es', 'Spanish'), ('en', 'English'), ('de', 'German'), ('fr', 'French'), ('it', 'Italian'), ('ru', 'Russian'))
        locales = fields.ListField(fields.StringField(choices=LOCALES), help_text=_("""List of languages for your application (the first one will be the default language)"""))


**forms.py**::

    class ContactInfoForm(DocumentForm):
        class Meta:
            document = ContactInfo
            widgets = {
                'web': URLInput(attrs={'class': 'form-control'}),
                'email': EmailInput(attrs={'class': 'form-control'}),
                'phone': TextInput(attrs={'class': 'form-control'})
            }

    class ApplicationForm(DocumentForm):
        contact = forms.fields.EmbeddedDocumentField(ContactInfoForm)
        class Meta:
            document = Application
            fields = ('name', 'locales', 'contact')
            widgets = {
                'name': TextInput(attrs={'class': 'form-control', 'required': 'required'}),
                'locales':  SelectMultiple(attrs={'class': 'form-control chosen-select', 'required': 'required'})
            }
