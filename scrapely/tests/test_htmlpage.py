"""
htmlpage.py tests
"""
import os
from unittest import TestCase

from scrapely import json
from scrapely.tests import path
from scrapely.htmlpage import parse_html, HtmlTag, HtmlDataFragment
from scrapely.tests.test_htmlpage_data import *

SAMPLES_FILE_PREFIX = os.path.join(path, "samples/samples_htmlpage")

def _encode_element(el):
    """
    jsonize parse element
    """
    if isinstance(el, HtmlTag):
        return {"tag": el.tag, "attributes": el.attributes,
            "start": el.start, "end": el.end, "tag_type": el.tag_type}
    if isinstance(el, HtmlDataFragment):
        return {"start": el.start, "end": el.end, "is_text_content": el.is_text_content}
    raise TypeError

def _decode_element(dct):
    """
    dejsonize parse element
    """
    if "tag" in dct:
        return HtmlTag(dct["tag_type"], dct["tag"], \
            dct["attributes"], dct["start"], dct["end"])
    if "start" in dct:
        return HtmlDataFragment(dct["start"], dct["end"], dct.get("is_text_content", True))
    return dct

class TestParseHtml(TestCase):
    """Test for parse_html"""
    def _test_sample(self, source, expected_parsed, samplecount=None):
        parsed = parse_html(source)
        count_element = 0
        count_expected = 0
        for element in parsed:
            if type(element) == HtmlTag:
                count_element += 1
            expected = expected_parsed.pop(0)
            if type(expected) == HtmlTag:
                count_expected += 1
            element_text = source[element.start:element.end]
            expected_text = source[expected.start:expected.end]
            if element.start != expected.start or element.end != expected.end:
                errstring = "[%s,%s] %s != [%s,%s] %s" % (element.start, \
                    element.end, element_text, expected.start, \
                    expected.end, expected_text)
                if samplecount is not None:
                    errstring += " (sample %d)" % samplecount
                assert False, errstring
            if type(element) != type(expected):
                errstring = "(%s) %s != (%s) %s for text\n%s" % (count_element, \
                    repr(type(element)), count_expected, repr(type(expected)), element_text)
                if samplecount is not None:
                    errstring += " (sample %d)" % samplecount
                assert False, errstring
            if type(element) == HtmlTag:
                self.assertEqual(element.tag, expected.tag)
                self.assertEqual(element.attributes, expected.attributes)
                self.assertEqual(element.tag_type, expected.tag_type)
            if type(element) == HtmlDataFragment:
                msg = "Got: %s Expected: %s in sample: %d [%d:%d] (%s)" % \
                        (element.is_text_content, expected.is_text_content, samplecount, element.start, element.end, repr(element_text)) \
                        if samplecount is not None else None
                self.assertEqual(element.is_text_content, expected.is_text_content, msg)

        if expected_parsed:
            errstring = "Expected %s" % repr(expected_parsed)
            if samplecount is not None:
                errstring += " (sample %d)" % samplecount
            assert False, errstring

    def test_parse(self):
        """simple parse_html test"""
        parsed = [_decode_element(d) for d in PARSED]
        sample = {"source": PAGE, "parsed": parsed}
        self._test_sample(PAGE, parsed)
        
    def test_site_samples(self):
        """test parse_html from real cases"""
        count = 0
        fname = "%s_%d.json" % (SAMPLES_FILE_PREFIX, count)
        while os.path.exists(fname):
            source = open("%s_%d.html" % (SAMPLES_FILE_PREFIX, count), "rb").read()
            source = source.decode('utf-8')
            parsed = json.loads(open(fname, "rb").read().decode('utf-8'), \
                    object_hook=_decode_element)
            self._test_sample(source, parsed, count)
            count += 1
            fname = "%s_%d.json" % (SAMPLES_FILE_PREFIX, count)
 
    def test_bad(self):
        """test parsing of bad html layout"""
        parsed = [_decode_element(d) for d in PARSED2]
        self._test_sample(PAGE2, parsed)

    def test_comments(self):
        """test parsing of tags inside comments"""
        parsed = [_decode_element(d) for d in PARSED3]
        self._test_sample(PAGE3, parsed)

    def test_script_text(self):
        """test parsing of tags inside scripts"""
        parsed = [_decode_element(d) for d in PARSED4]
        self._test_sample(PAGE4, parsed)
        
    def test_sucessive(self):
        """test parsing of sucesive cleaned elements"""
        parsed = [_decode_element(d) for d in PARSED5]
        self._test_sample(PAGE5, parsed)
        
    def test_sucessive2(self):
        """test parsing of sucesive cleaned elements (variant 2)"""
        parsed = [_decode_element(d) for d in PARSED6]
        self._test_sample(PAGE6, parsed)
    
    def test_special_cases(self):
        """some special cases tests"""
        parsed = list(parse_html("<meta http-equiv='Pragma' content='no-cache' />"))
        self.assertEqual(parsed[0].attributes, {'content': 'no-cache', 'http-equiv': 'Pragma'})
        parsed = list(parse_html("<html xmlns='http://www.w3.org/1999/xhtml' xml:lang='en' lang='en'>"))
        self.assertEqual(parsed[0].attributes, {'xmlns': 'http://www.w3.org/1999/xhtml', 'xml:lang': 'en', 'lang': 'en'})
        parsed = list(parse_html("<IMG SRC='http://images.play.com/banners/SAM550a.jpg' align='left' / hspace=5>"))
        self.assertEqual(parsed[0].attributes, {'src': 'http://images.play.com/banners/SAM550a.jpg', \
                                                'align': 'left', 'hspace': '5', '/': None})

    def test_no_ending_body(self):
        """Test case when no ending body nor html elements are present"""
        parsed = [_decode_element(d) for d in PARSED7]
        self._test_sample(PAGE7, parsed)

    def test_malformed(self):
        """Test parsing of some malformed cases"""
        parsed = [_decode_element(d) for d in PARSED8]
        self._test_sample(PAGE8, parsed)

    def test_malformed2(self):
        """Test case when attributes are not separated by space (still recognizable because of quotes)"""
        parsed = [_decode_element(d) for d in PARSED9]
        self._test_sample(PAGE9, parsed)

