from unittest import TestCase
from cStringIO import StringIO

from scrapely import Scraper
from scrapely.htmlpage import HtmlPage
from scrapely.tests import iter_samples

class ScraperTest(TestCase):
    
    def _assert_extracted(self, extracted, expected):
        # FIXME: this is a very weak test - we should assert the 
        # extracted data matches, fixing issues that prevent it
        expect_keys = sorted(expected.keys())
        found_keys = sorted(extracted[0].keys())
        self.assertEqual(expect_keys, found_keys)

    def test_extraction(self):

        samples_encoding = 'latin1'
        [(html1, data1), (html2, data2)] = list(iter_samples(
            'scraper_loadstore', html_encoding=samples_encoding))
        sc = Scraper()
        page1 = HtmlPage(body=html1, encoding=samples_encoding)
        sc.train_from_htmlpage(page1, data1)

        page2 = HtmlPage(body=html2, encoding=samples_encoding)
        extracted_data = sc.scrape_page(page2)
        self._assert_extracted(extracted_data, data2)

        # check still works after serialize/deserialize 
        f = StringIO()
        sc.tofile(f)
        f.seek(0)
        sc = Scraper.fromfile(f)
        extracted_data = sc.scrape_page(page2)
        self._assert_extracted(extracted_data, data2)
