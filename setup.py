import os
import sys
from pathlib import Path

from setuptools import find_packages, setup

_directory = Path(__file__).parent

__version__ = (_directory / "VERSION").read_text().strip()
__description__ = 'Django support for MongoDB via MongoEngine'
__license__ = 'BSD'
__author__ = 'Ross Lawley'
__email__ = 'ross.lawley@gmail.com'


sys.path.insert(0, os.path.dirname(__file__))


setup(
    name='django-mongoengine',
    version=__version__,
    url='https://github.com/mongoengine/django-mongoengine',
    download_url='https://github.com/mongoengine/django-mongoengine/tarball/master',
    license=__license__,
    author=__author__,
    author_email=__email__,
    description=__description__,
    long_description=(_directory / "README.rst").read_text().strip(),
    long_description_content_type="text/x-rst",
    zip_safe=False,
    platforms='any',
    install_requires=["Django>3.1,<4.1", "mongoengine>=0.14"],
    packages=find_packages(
        exclude=(
            'doc',
            'docs',
        )
    ),
    include_package_data=True,
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Framework :: Django',
    ],
)
