"""
Test MDR extractor.
"""
from unittest import TestCase, SkipTest
from scrapely.extraction import InstanceBasedLearningExtractor
from scrapely.extraction.regionextract import (BasicTypeExtractor, TraceExtractor, RepeatedDataExtractor, MdrExtractor,
                                              AdjacentVariantExtractor, RecordExtractor, TemplatePageExtractor)
from scrapely.extraction.pageparsing import parse_strings
from scrapely.descriptor import FieldDescriptor, ItemDescriptor
from scrapely.htmlpage import HtmlPage

from . import get_page

def _get_value_with_xpath(html, xpath):
    from lxml.html import document_fromstring
    return document_fromstring(html).xpath(xpath)[0]

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
            from mdr import MDR
        except ImportError:
            raise SkipTest("MDR is not available")
        template, _ = parse_strings(get_page('mdrparsing_template_0'), u'')
        descriptor = FieldDescriptor('text', None, lambda x: x.strip())
        ex = BasicTypeExtractor(template.annotations[-1], {'text': descriptor})
        extractor = MdrExtractor.apply(template, [ex])[0]
        self.assertTrue(isinstance(extractor, MdrExtractor))
        for element in extractor.record:
            self.assertTrue(element.xpath('descendant-or-self::*[@data-scrapy-annotate]'), 'annnotation should be propagated')


    def test_extract(self):
        try:
            from mdr import MDR
        except ImportError:
            raise SkipTest("MDR is not available")

        template, page = parse_strings(get_page('mdrparsing_template_0'), get_page('mdrparsing_page_0'))

        d1 = FieldDescriptor('text', None, lambda x: x.strip())
        d2 = FieldDescriptor('date', None, lambda x: x.strip())

        ex1 = BasicTypeExtractor(template.annotations[-1], {'text': d1})
        ex2 = BasicTypeExtractor(template.annotations[-2], {'date': d2})

        extractor = MdrExtractor.apply(template, [ex1, ex2])[0]
        items = extractor.extract(page)[0].values()[0]

        self.assertEqual(len(items), 40)

        # extracted items are orderred
        self.assertEquals(_get_value_with_xpath(items[0]['date'][0], '//meta/@content'), '2014-07-02')
        self.assertEquals(_get_value_with_xpath(items[-1]['date'][0], '//meta/@content'), '2014-05-18')

    def test_extract2(self):
        try:
            from mdr import MDR
        except ImportError:
            raise SkipTest("MDR is not available")

        template, page = parse_strings(get_page('mdrparsing_template_1'), get_page('mdrparsing_page_1'))

        d1 = FieldDescriptor('review', None, lambda x: x.strip())
        ex1 = BasicTypeExtractor(template.annotations[-1], {'review': d1})

        extractor = MdrExtractor.apply(template, [ex1])[0]
        items = extractor.extract(page)[0].values()[0]
        self.assertEqual(len(items), 6)

        # extracted items are orderred
        self.assertEquals(items[0]['review'][0], "Although it's expensive book I think it "
            "worth the money as it is the \"Bible\" of Machine Learning and Pattern recognition. However, "
            "has a lot of mathematics meaning that a strong mathematical background is necessary. "
            "I suggest it especially for PhD candidates in this field.")

        self.assertEquals(items[-1]['review'][0], "As a newbie to pattern recognition I found this book very helpful. "
            "It is the clearest book I ever read! Accompanying examples and material are very illuminating. "
            "I particularly appreciated the gradual introduction of key concepts, often accompanied with practical "
            "examples and stimulating exercises.")

    def test_ibl_extraction(self):
        try:
            from mdr import MDR
        except ImportError:
            raise SkipTest("MDR is not available")

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

        self.assertEqual(len(actual_output[0].get('default_group')), 40)

        # extracted items are orderred
        self.assertEquals(_get_value_with_xpath(actual_output[0].get('default_group')[0]['date'][0], '//meta/@content'), '2014-07-02')
        self.assertEquals(_get_value_with_xpath(actual_output[0].get('default_group')[-1]['date'][0], '//meta/@content'), '2014-05-18')
