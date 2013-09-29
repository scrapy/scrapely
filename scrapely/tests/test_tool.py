# encoding: utf8

from unittest import TestCase

from scrapely.htmlpage import HtmlPage
from scrapely.template import TemplateMaker
from scrapely.tool import parse_criteria, apply_criteria, readable_repr


class ToolCJKTestCase(TestCase):

    PAGE = HtmlPage("http://www.example.com", body=u"""
    <html>
      <body>
        <h1>标题</h1>
        <p>段落</p>
        <h2>另一个标题</h2>
        <p>另一个段落</p>
      </body>
    </html>
    """)

    def test_apply_criteria_should_support_cjk_chars(self):
        criteria = parse_criteria('标题')
        tm = TemplateMaker(self.PAGE)

        selection = apply_criteria(criteria, tm)

        self.assertEqual(selection, [6, 14])
        self.assertEqual(tm.selected_data(6), u'<h1>标题</h1>')
        self.assertEqual(tm.selected_data(14), u'<h2>另一个标题</h2>')


class ReadableReprTextCase(TestCase):

    def test_readable_repr(self):
        cjk = u'cjk\t中日韩\n\\u535a'
        readable = u"u'cjk\\t中日韩\\n\\\\u535a'"

        self.assertEqual(readable_repr(cjk), readable)
