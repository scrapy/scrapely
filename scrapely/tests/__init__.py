import sys
from os import path
from itertools import count
from unittest import TestSuite, TestLoader, main
from doctest import DocTestSuite
from scrapely import json

_PATH  = path.abspath(path.dirname(__file__))

def iter_samples(prefix, html_encoding='utf-8', **json_kwargs):
    """Iterate through (raw_data, extracted_data) for all samples
    beginning with the specified prefix.

    By convention, these are stored in the samples directory in the 
    format samples_PREFIX_COUNTER.[html|json]
    """
    SAMPLES_FILE_PREFIX = path.join(_PATH, "samples/samples_" + prefix + "_")
    json_load_kwargs = dict(encoding='utf-8')
    json_load_kwargs.update(json_kwargs)
    for i in count():
        fname = SAMPLES_FILE_PREFIX + str(i)
        html_page = fname + ".html"
        if not path.exists(html_page):
            return
        html_str = open(html_page, 'rb').read()
        sample_data = json.load(open(fname + '.json'), **json_load_kwargs)
        yield html_str.decode(html_encoding), sample_data

UNIT_TESTS = [
    'scrapely.tests.test_extraction',
    'scrapely.tests.test_htmlpage',
    'scrapely.tests.test_htmlpage_data',
    'scrapely.tests.test_pageparsing',
    'scrapely.tests.test_template',
    'scrapely.tests.test_scraper',
]

DOC_TESTS = [
    'scrapely.extractors',
    'scrapely.extraction.regionextract',
    'scrapely.extraction.similarity',
    'scrapely.extraction.pageobjects',
]

def suite():
    suite = TestSuite()
    for m in UNIT_TESTS:
        suite.addTests(TestLoader().loadTestsFromName(m))
    for m in DOC_TESTS:
        suite.addTest(DocTestSuite(__import__(m, {}, {}, [''])))
    return suite

