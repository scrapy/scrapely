from unittest import TestCase

from scrapely.htmlpage import HtmlPage
from scrapely.template import TemplateMaker, FragmentNotFound, \
    FragmentAlreadyAnnotated, best_match
from scrapely.extraction import InstanceBasedLearningExtractor

class TemplateMakerTest(TestCase):

    PAGE = HtmlPage("http://www.example.com", body=u"""
    <html>
      <body>
        <h1>Some title</h1>
        <p>Some text to annotate here</p>
        <h2>Another title</h2>
        <p>Another text to annotate there</p>
        <p>More text with unpaired tag <img />and that's it</p>
      </body>
    </html>
    """)

    def test_annotate_single(self):
        tm = TemplateMaker(self.PAGE)
        tm.annotate('field1', best_match('text to annotate'))
        tpl = tm.get_template()
        ex = InstanceBasedLearningExtractor([tpl])
        self.assertEqual(ex.extract(self.PAGE)[0],
            [{u'field1': [u'Some text to annotate here']}])

    def test_annotate_multiple(self):
        tm = TemplateMaker(self.PAGE)
        tm.annotate('field1', best_match('text to annotate'), best_match=False)
        tpl = tm.get_template()
        ex = InstanceBasedLearningExtractor([tpl])
        self.assertEqual(ex.extract(self.PAGE)[0],
            [{u'field1': [u'Some text to annotate here', u'Another text to annotate there']}])

    def test_annotate_ignore_unpaired(self):
        tm = TemplateMaker(self.PAGE)
        tm.annotate('field1', best_match("and that's"), best_match=False)
        tpl = tm.get_template()
        ex = InstanceBasedLearningExtractor([tpl])
        self.assertEqual(ex.extract(self.PAGE)[0],
            [{u'field1': [u"More text with unpaired tag <img />and that's it"]}])

    def test_annotate_fragment_not_found(self):
        tm = TemplateMaker(self.PAGE)
        self.assertRaises(FragmentNotFound, tm.annotate, 'field1', best_match("missing text"))

    def test_annotate_fragment_already_annotated(self):
        tm = TemplateMaker(self.PAGE)
        tm.annotate('field1', best_match('text to annotate'))
        self.assertRaises(FragmentAlreadyAnnotated, tm.annotate, 'field1', best_match("text to annotate"))

    def test_selected_data(self):
        tm = TemplateMaker(self.PAGE)
        indexes = tm.select(best_match('text to annotate'))
        data = [tm.selected_data(i) for i in indexes]
        self.assertEqual(data, \
            [u'<p>Some text to annotate here</p>', \
            u'<p>Another text to annotate there</p>'])

    def test_annotations(self):
        tm = TemplateMaker(self.PAGE)
        tm.annotate('field1', best_match('text to annotate'), best_match=False)
        annotations = [x[0] for x in tm.annotations()]
        self.assertEqual(annotations,
            [{u'annotations': {u'content': u'field1'}},
             {u'annotations': {u'content': u'field1'}}])

    def test_best_match(self):
        self.assertEquals(self._matches('text to annotate'),
            ['Some text to annotate here', 'Another text to annotate there'])

    def _matches(self, text):
        bm = best_match(text)
        matches = [(bm(f, self.PAGE), f) for f in self.PAGE.parsed_body]
        matches = [x for x in matches if x[0]]
        matches.sort(reverse=True)
        return [self.PAGE.fragment_data(x[1]) for x in matches]
