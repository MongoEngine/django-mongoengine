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
import sys, os

sys.path.insert(0, os.path.dirname(__file__))

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
              'django_mongoengine.debug_toolbar',
              'django_mongoengine.forms',
              'django_mongoengine.utils',
              'django_mongoengine.views'],
    include_package_data=True,
    # use python setup.py nosetests to test
    setup_requires=['nose', 'coverage'],
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
