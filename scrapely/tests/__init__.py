import sys
from unittest import TestSuite, TestLoader, main
from doctest import DocTestSuite

path = sys.modules[__name__].__path__[0]

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

