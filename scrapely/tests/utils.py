"""
tests for page parsing

Page parsing effectiveness is measured through the evaluation system. These
tests should focus on specific bits of functionality work correctly.
"""
from unittest import TestCase

from scrapely.htmlpage import HtmlPage
from scrapely.extraction import InstanceBasedLearningExtractor

class _TestIblBase(TestCase):

    TESTCASE_DATA = []
    def _run_extraction(self, name, templates, page, descriptor, expected_output):
        self.trace = None
        template_pages = [HtmlPage(None, {}, t) for t in templates]
        # extracts with trace enabled in order to generate traceback
        extractor = InstanceBasedLearningExtractor([(t, descriptor) for t in template_pages], True)
        actual_output, _ = extractor.extract(HtmlPage(None, {}, page))
        if actual_output is not None:
            actual_output = actual_output[0]
            self.trace = ["Extractor:\n%s" % extractor] + actual_output.pop('trace')
        # extracts again with trace disabled in order to get the pure output
        extractor = InstanceBasedLearningExtractor([(t, descriptor) for t in template_pages])
        actual_output, _ = extractor.extract(HtmlPage(None, {}, page))
        if actual_output is None:
            if expected_output is None:
                return
            assert False, "failed to extract data for test '%s'" % name
        else:
            actual_output = actual_output[0]
        expected_names = set(expected_output.keys())
        actual_names = set(actual_output.keys())
        
        missing_in_output = filter(None, expected_names - actual_names)
        error = "attributes '%s' were expected but were not present in test '%s'" % \
                ("', '".join(missing_in_output), name)
        assert len(missing_in_output) == 0, error

        unexpected = actual_names - expected_names
        error = "unexpected attributes %s in test '%s'" % \
                (', '.join(unexpected), name)
        assert len(unexpected) == 0, error

        for k, v in expected_output.items():
            extracted = actual_output[k]
            assert v == extracted, "in test '%s' for attribute '%s', " \
                "expected value '%s' but got '%s'" % (name, k, v, extracted)

    def test_expected_outputs(self):
        try:
            for data in self.TESTCASE_DATA:
                self._run_extraction(*data)
        except AssertionError:
            if self.trace:
                print "Trace:"
                for line in self.trace:
                    print "\n---\n%s" % line
            raise
