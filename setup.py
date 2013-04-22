import sys

args = dict(
    name='scrapely',
    version='0.10',
    license='BSD',
    description='A pure-python HTML screen-scraping library',
    author='Scrapy project',
    author_email='info@scrapy.org',
    url='http://github.com/scrapy/scrapely',
    packages=['scrapely', 'scrapely.extraction'],
    platforms=['Any'],
    classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing :: Markup :: HTML',
    ]
)

try:
    from setuptools import setup
    args['install_requires'] = ['numpy', 'w3lib']
    if sys.version_info < (2, 6):
        args['install_requires'] += ['simplejson']
except ImportError:
    from distutils.core import setup

setup(**args)

