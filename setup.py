#!/usr/bin/env python
import os
import platform
from setuptools import setup, find_packages
from setuptools.extension import Extension


USE_CYTHON = 'CYTHONIZE' in os.environ
IS_PYPY = platform.python_implementation() == 'PyPy'
ext = '.pyx' if USE_CYTHON else '.c'
try:
    import numpy as np
    include_dirs = [np.get_include()]
except ImportError:
    include_dirs = []
extensions = [
    Extension("scrapely._htmlpage",
              ["scrapely/_htmlpage%s" % ext],
              include_dirs=include_dirs),
    Extension("scrapely.extraction._similarity",
              ["scrapely/extraction/_similarity%s" % ext],
              include_dirs=include_dirs),
]
if USE_CYTHON and not IS_PYPY:
    from Cython.Build import cythonize
    extensions = cythonize(extensions)
if IS_PYPY:
    extensions = []


setup(
    name='scrapely',
    version='0.13.2',
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
    extras_require={
        'speedup': ['cython']
    },
    ext_modules=extensions,
)
