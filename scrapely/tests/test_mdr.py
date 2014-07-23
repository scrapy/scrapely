"""
Test MDR.
"""
from unittest import TestCase, SkipTest
from scrapely.extraction import InstanceBasedLearningExtractor
from scrapely.extraction.regionextract import (BasicTypeExtractor, TraceExtractor, RepeatedDataExtractor, MdrExtractor,
                                              AdjacentVariantExtractor, RecordExtractor, TemplatePageExtractor)
from scrapely.extraction.pageparsing import parse_strings
from scrapely.descriptor import FieldDescriptor, ItemDescriptor

from scrapely.htmlpage import HtmlPage
from scrapely.tests import get_page

class MdrIBL(InstanceBasedLearningExtractor):

    def build_extraction_tree(self, template, type_descriptor, trace=True):
        """Build a tree of region extractors corresponding to the
        template
        """
        attribute_map = type_descriptor.attribute_map if type_descriptor else None
        extractors = BasicTypeExtractor.create(template.annotations, attribute_map)
        mdr_extractor, extractors = MdrExtractor.apply(template, extractors)

        if trace:
            extractors = TraceExtractor.apply(template, extractors)
        for cls in (RepeatedDataExtractor, AdjacentVariantExtractor, RepeatedDataExtractor, AdjacentVariantExtractor, RepeatedDataExtractor,
                    RecordExtractor):
            extractors = cls.apply(template, extractors)
            if trace:
                extractors = TraceExtractor.apply(template, extractors)

        if mdr_extractor:
            extractors.append(mdr_extractor)

        return TemplatePageExtractor(template, extractors)

class TestMdrExtractor(TestCase):

    def test_detect(self):
        try:
            from mdr.mdr import MDR
        except ImportError:
            raise SkipTest("mdr is not available")
        template, _ = parse_strings(get_page('mdrparsing_template_0'), u'')
        descriptor = FieldDescriptor('text', None, lambda x: x.strip())
        ex = BasicTypeExtractor(template.annotations[-1], {'text': descriptor})
        extractors = MdrExtractor.apply(template, [ex])
        self.assertTrue(isinstance(extractors[0], MdrExtractor))

    def test_extract(self):
        try:
            from mdr.mdr import MDR
        except ImportError:
            raise SkipTest("mdr is not available")

        template, page = parse_strings(get_page('mdrparsing_template_0'), get_page('mdrparsing_page_0'))

        d1 = FieldDescriptor('text', None, lambda x: x.strip())
        d2 = FieldDescriptor('date', None, lambda x: x.strip())

        ex1 = BasicTypeExtractor(template.annotations[-1], {'text': d1})
        ex2 = BasicTypeExtractor(template.annotations[-2], {'date': d2})

        extractor = MdrExtractor.apply(template, [ex1, ex2])[0]
        items = extractor.extract(page)[0]

        self.assertEqual(len(items['date']), 40)
        self.assertEqual(len(items['text']), 40)

    def test_ibl_extraction(self):
        try:
            from mdr.mdr import MDR
        except ImportError:
            raise SkipTest("mdr is not available")

        template = HtmlPage(None, {}, get_page('mdrparsing_template_0'))
        page = HtmlPage(None, {}, get_page('mdrparsing_page_0'))

        descriptor = ItemDescriptor('test',
                'item test, removes tags from description attribute',
                [FieldDescriptor('text', None, lambda x: x.strip()),
                FieldDescriptor('date', None, lambda x: x.strip())])

        extractor = MdrIBL([(template, descriptor)])
        actual_output, _ = extractor.extract(page)
        self.assertEqual(actual_output[0].get('name')[0].strip(), 'Gary Danko')
        self.assertEqual(actual_output[0].get('phone')[0].strip(), '(415) 749-2060')
        self.assertEqual(len(actual_output[0].get('date')), 40)
        self.assertEqual(len(actual_output[0].get('text')), 40)
