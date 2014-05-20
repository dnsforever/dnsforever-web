#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='dnsforever',
    version='0.1',
    packages=find_packages(),
    zip_safe=False,
    install_requires=['Flask>=0.10.1',
                      'Flask-Script>=2.0.3',
                      'Flask-WTF>=0.9.5',
                      'Werkzeug>=0.7',
                      'Jinja2>=2.4',
                      'SQLAlchemy>=0.9.4']
)
