import urllib
try:
    import json
except ImportError:
    import simplejson as json

from scrapely.htmlpage import HtmlPage, page_to_dict
from scrapely.template import TemplateMaker, best_match
from scrapely.extraction import InstanceBasedLearningExtractor

class Scraper(object):

    def __init__(self, templates=None):
        """Initialize an empty scraper."""
        self.templates = templates or []

    @classmethod
    def fromfile(cls, file):
        """Initialize a scraper from a file previously stored by tofile()
        method.
        """
        templates = [HtmlPage(**x) for x in json.load(file)['templates']]
        return cls(templates)

    def tofile(self, file):
        """Store the scraper into the given file-like object"""
        tpls = [page_to_dict(x) for x in self.templates]
        json.dump({'templates': tpls}, file)

    def train(self, url, data, encoding='utf-8'):
        assert data, "Cannot train with empty data"
        page = self._get_page(url, encoding)
        tm = TemplateMaker(page)
        for field, values in data.items():
            if not hasattr(values, '__iter__'):
                values = [values]
            for value in values:
                if isinstance(value, str):
                    value = value.decode(encoding)
                tm.annotate(field, best_match(value))
        self.templates.append(tm.get_template())

    def scrape(self, url, encoding='utf-8'):
        page = self._get_page(url, encoding)
        ex = InstanceBasedLearningExtractor(self.templates)
        return ex.extract(page)[0]

    @staticmethod
    def _get_page(url, encoding):
        body = urllib.urlopen(url).read().decode(encoding)
        return HtmlPage(url, body=body, encoding=encoding)
