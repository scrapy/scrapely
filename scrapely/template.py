import copy
import json

from scrapely.htmlpage import HtmlTag, HtmlTagType


class AnnotationError(Exception):
    pass


class FragmentNotFound(AnnotationError):
    pass


class FragmentAlreadyAnnotated(AnnotationError):
    pass


class TemplateMaker(object):

    def __init__(self, htmlpage):
        self.htmlpage = copy.copy(htmlpage)

    def annotate(self, field, score_func, best_match=True):
        """Annotate a field.

        ``score_func`` is a callable that receives two arguments: (fragment,
        htmlpage) and returns a relevancy score (float) indicating how relevant
        is the fragment. 0 means the fragment is irrelevant. Higher scores
        means the fragment is more relevant. Otherwise, the closest opening tag
        (to the left) is annotated with the given attribute.

        If ``best_match`` is ``True``, only the best fragment is annotated.
        Otherwise, all fragments (with a positive relevancy) are annotated.

        """
        indexes = self.select(score_func)
        if not indexes:
            raise FragmentNotFound("Fragment not found annotating %r using: %s" %
                (field, score_func))
        if best_match:
            del indexes[1:]
        for i in indexes:
            self.annotate_fragment(i, field)

    def select(self, score_func):
        """Return the indexes of fragment where score_func returns a positive
        value, reversely sorted by that value"""
        htmlpage = copy.copy(self.htmlpage)
        matches = []
        for i, fragment in enumerate(htmlpage.parsed_body):
            score = score_func(fragment, htmlpage)
            if score:
                matches.append((score, i))
        matches.sort(reverse=True)
        return [x[1] for x in matches]

    def selected_data(self, index):
        """Return the data that would be annotated from the given fragment
        index
        """
        start_tag, end_tag = _enclosing_tags(self.htmlpage, index)
        return self.htmlpage.body[start_tag.start:end_tag.end]

    def annotations(self):
        """Return all annotations contained in the template as a list of tuples
        (annotation, index)
        """
        anlist = []
        for i, f in enumerate(self.htmlpage.parsed_body):
            if isinstance(f, HtmlTag) and f.tag_type == HtmlTagType.OPEN_TAG:
                at = f.attributes.get('data-scrapy-annotate')
                if at:
                    an = json.loads(at.replace('&quot;', '"'))
                    anlist.append((an, i))
        return anlist

    def annotate_fragment(self, index, field):
        for f in self.htmlpage.parsed_body[index::-1]:
            if isinstance(f, HtmlTag) and f.tag_type == HtmlTagType.OPEN_TAG:
                if 'data-scrapy-annotate' in f.attributes:
                    fstr = self.htmlpage.fragment_data(f)
                    raise FragmentAlreadyAnnotated("Fragment already annotated: %s" % fstr)
                d = {'annotations': {'content': field}}
                a = ' data-scrapy-annotate="%s"' % json.dumps(d).replace('"', '&quot;')
                p = self.htmlpage
                p.body = p.body[:f.end-1] + a + p.body[f.end-1:]
                return True
        return False

    def get_template(self):
        """Return the generated template as a HtmlPage object"""
        return self.htmlpage


def best_match(text):
    """Function to use in TemplateMaker.annotate()"""
    def func(fragment, page):
        fdata = page.fragment_data(fragment).strip()
        if text in fdata:
            return float(len(text)) / len(fdata) - (1e-6 * fragment.start)
        else:
            return 0.0
    return func


def _enclosing_tags(htmlpage, index):
    f = htmlpage.parsed_body[index]
    if isinstance(f, HtmlTag) and f.tag_type == HtmlTagType.UNPAIRED_TAG:
        return f, f
    start_tag = end_tag = None
    for f in htmlpage.parsed_body[index::-1]:
        if isinstance(f, HtmlTag) and f.tag_type == HtmlTagType.OPEN_TAG:
            start_tag = f
            break
    if not start_tag:
        raise FragmentNotFound("Unable to find start tag from index %d" % index)
    tcount = 1
    start_index = htmlpage.parsed_body.index(start_tag)
    for f in htmlpage.parsed_body[start_index+1:]:
        if isinstance(f, HtmlTag) and f.tag == start_tag.tag:
            if f.tag_type == HtmlTagType.OPEN_TAG:
                tcount += 1
            if f.tag_type == HtmlTagType.CLOSE_TAG:
                tcount -= 1
                if not tcount:
                    end_tag = f
                    break
    if not end_tag or htmlpage.parsed_body.index(end_tag) < index:
        # end tag not found or tag found is not enclosing
        return f, f
    return start_tag, end_tag
