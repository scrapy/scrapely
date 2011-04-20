========
scrapely
========

Scrapely is a library for extracting structured data from HTML pages. Given
some example web pages and the data to be extracted, scrapely constructs a
parser for all similar pages.

Usage (API)
===========

Scrapely has a powerful API, including a template format that can be edited
externally, that you can use to build very capable scrapers.

What follows is a quick example of the simplest possible usage, that you can
run in the Python shell. This example is also available in the ``example.py``
script, located at the root of the repository.

Start by importing and instantiating the Scraper class::

    >>> from scrapely import Scraper
    >>> s = Scraper()

Then, proceed to train the scraper by adding some page and the data you expect
to scrape from there::

    >>> url1 = 'http://pypi.python.org/pypi/w3lib'
    >>> data = {'name': 'w3lib 1.0', 'author': 'Scrapy project', 'description': 'Library of web-related functions'}
    >>> s.train(url1, data)

Finally, tell the scraper to scrape any other similar page and it will return
the results::

    >>> url2 = 'http://pypi.python.org/pypi/Django/1.3'
    >>> s.scrape(url2)
    [{u'author': [u'Django Software Foundation &lt;foundation at djangoproject com&gt;'],
      u'description': [u'A high-level Python Web framework that encourages rapid development and clean, pragmatic design.'],
      u'name': [u'Django 1.3']}]

That's it! No xpaths, regular expressions, or hacky python code.

Usage (command line tool)
=========================

There is also a simple script to create and manage Scrapely scrapers.

It supports a command-line interface, and an interactive prompt. All commands
supported on interactive prompt are also supported in the command-line
interface.

To enter the interactive prompt type the following without arguments::

    python -m scrapely.tool myscraper.json

Example::

    $ python -m scrapely.tool myscraper.json
    scrapely> help

    Documented commands (type help <topic>):
    ========================================
    a  al  s  ta  td  tl

    scrapely> 

To create a scraper and add a template::

    scrapely> ta http://pypi.python.org/pypi/w3lib
    [0] http://pypi.python.org/pypi/w3lib

This is equivalent as typing the following in one command::

    python -m scrapely.tool myscraper.json ta http://pypi.python.org/pypi/w3lib

To list available templates from a scraper::

    scrapely> tl
    [0] http://pypi.python.org/pypi/w3lib

To add a new annotation, you usually test the selection criteria first::

    scrapely> a 0 w3lib 1.0
    [0] u'<a href="/pypi/w3lib/1.0">w3lib 1.0</a>'
    [1] u'<h1>w3lib 1.0</h1>'
    [2] u'<title>Python Package Index : w3lib 1.0</title>'
    
You can refine by position. To take the one in position [1]::

    scrapely> a 0 w3lib 1.0 -n 1
    [0] u'<h1>w3lib 1.0</h1>'

To annotate some fields on the template::

    scrapely> a 0 w3lib 1.0 -n 1 -f name
    [new] (name) u'<h1>w3lib 1.0</h1>'
    scrapely> a 0 Scrapy project -n 1 -f author
    [new] u'<span>Scrapy project &lt;info at scrapy org&gt;</span>'

To list annotations on a template::

    scrapely> al 0
    [0-0] (name) u'<h1>w3lib 1.0</h1>'
    [0-1] (author) u'<span>Scrapy project &lt;info at scrapy org&gt;</span>'

To scrape another similar page with the already added templates::

    scrapely> s http://pypi.python.org/pypi/Django/1.3
    [{u'author': [u'Django Software Foundation &lt;foundation at djangoproject com&gt;'],
      u'name': [u'Django 1.3']}]


Requirements
============

    * numpy
    * w3lib
    * simplejson or Python 2.6+


Installation
============

To install scrapely on any platform use::

    pip install scrapely

If you're using Ubuntu (9.10 or above), you can install scrapely from the
Scrapy Ubuntu repos. Just add the Ubuntu repos as described here:
http://doc.scrapy.org/topics/ubuntu.html

And then install scrapely with::

    aptitude install python-scrapely


Architecture
============

Unlike most scraping libraries, Scrapely doesn't work with DOM trees or xpaths
so it doesn't depend on libraries such as lxml or libxml2. Instead, it uses
an internal pure-python parser, which can accept poorly formed HTML. The HTML is
converted into an array of token ids, which is used for matching the items to
be extracted.

Scrapely extraction is based upon the Instance Based Learning algorithm [1]_
and the matched items are combined into complex objects (it supports nested and
repeated objects), using a tree of parsers, inspired by A Hierarchical
Approach to Wrapper Induction [2]_.

.. [1] `Yanhong Zhai , Bing Liu, Extracting Web Data Using Instance-Based Learning, World Wide Web, v.10 n.2, p.113-132, June 2007 <http://portal.acm.org/citation.cfm?id=1265174>`_

.. [2] `Ion Muslea , Steve Minton , Craig Knoblock, A hierarchical approach to wrapper induction, Proceedings of the third annual conference on Autonomous Agents, p.190-197, April 1999, Seattle, Washington, United States <http://portal.acm.org/citation.cfm?id=301191>`_

Known Issues
============

The training implementation is currently very simple and is only provided for
references purposes, to make it easier to test Scrapely and play with it. On
the other hand, the extraction code is reliable and production-ready. So, if
you want to use Scrapely in production, you should use train() with caution and
make sure it annotates the area of the page you intent being annotated.

Alternatively, you can use the Scrapely tool to annotate pages.

License
=======

Scrapely library is licensed under the BSD license.
