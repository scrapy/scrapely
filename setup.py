#!/usr/bin/env python
import os
from setuptools import setup, find_packages
from setuptools.extension import Extension
import numpy as np


USE_CYTHON = 'CYTHONIZE' in os.environ
ext = '.pyx' if USE_CYTHON else '.c'
extensions = [
    Extension("scrapely._htmlpage",
              ["scrapely/_htmlpage%s" % ext],
              include_dirs=[np.get_include()]),
    Extension("scrapely.extraction._similarity",
              ["scrapely/extraction/_similarity%s" % ext],
              include_dirs=[np.get_include()]),
]
if USE_CYTHON:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)


setup(
    name='scrapely',
    version='0.12.0',
    license='BSD',
    description='A pure-python HTML screen-scraping library',
    author='Scrapy project',
    author_email='info@scrapy.org',
    url='https://github.com/scrapy/scrapely',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    install_requires=['numpy', 'w3lib', 'six'],
    ext_modules=extensions,
)
