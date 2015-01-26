from setuptools import setup, find_packages

setup(
    name='scrapely',
    version='0.12.0',
    license='BSD',
    description='A pure-python HTML screen-scraping library',
    author='Scrapy project',
    author_email='info@scrapy.org',
    url='http://github.com/scrapy/scrapely',
    packages=find_packages(exclude=['tests', 'tests.*']),
    include_package_data=True,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Text Processing :: Markup :: HTML',
    ],
    install_requires=['numpy', 'w3lib'],
)
