"""
Django-MongoEngine
------------------

Django support for MongoDB using MongoEngine.

Links
`````

* `development version
  <https://github.com/MongoEngine/django-mongoengine/raw/master#egg=Django-MongoEngine-dev>`_

"""
from setuptools import setup

# Stops exit traceback on tests
try:
    import multiprocessing
except:
   pass

setup(
    name='django-mongoengine',
    version='0.3',
    url='https://github.com/mongoengine/django-mongoengine',
    license='BSD',
    author='Ross Lawley',
    author_email='ross.lawley@gmail.com',
    description='Django support for MongoDB via MongoEngine',
    long_description=__doc__,
    test_suite='nose.collector',
    zip_safe=False,
    platforms='any',
    install_requires=[
        'Django>=1.3',
        'mongoengine'
    ],
    packages=['django_mongoengine',
              'django_mongoengine.forms'],
    include_package_data=True,
    tests_require=[
        'nose',
    ],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django'
    ]
)
