#!/usr/bin/env python3

from setuptools import setup, find_packages

setup(
    name="openssh-ldap-authkeys",
    version="0.1.0",
    license='MIT',
    packages=find_packages(),
    scripts=['openssh-ldap-authkeys'],
    install_requires=[
        'dnspython>=1.0.0',
        'python-ldap>=3.0.0',
        'PyYAML>=3.0',
    ],
    author='Dan Fuhry',
    author_email='dan@fuhry.com',
    url='https://github.com/fuhry/openssh-ldap-authkeys',
    data_files=[
        ('/etc/openssh-ldap-authkeys', ['olak.yml.example', 'authmap.example']),
        ('/usr/lib/tmpfiles.d', ['openssh-ldap-authkeys.tmpfiles.conf']),
    ]
)
