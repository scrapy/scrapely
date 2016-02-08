"""
htmlpage

Container objects for representing html pages and their parts in the IBL
system. This encapsulates page related information and prevents parsing
multiple times.
"""
import re
import hashlib
import six

from six.moves.urllib.request import urlopen
from copy import deepcopy
from w3lib.encoding import html_to_unicode

import _htmlpage


parse_html = _htmlpage.parse_html
HtmlDataFragment = _htmlpage.HtmlDataFragment
HtmlTag = _htmlpage.HtmlTag
HtmlTagType = _htmlpage.HtmlTagType


def url_to_page(url, encoding=None, default_encoding='utf-8'):
    """Fetch a URL, using python urllib2, and return an HtmlPage object.

    The `url` may be a string, or a `urllib2.Request` object. The `encoding`
    argument can be used to force the interpretation of the page encoding.

    Redirects are followed, and the `url` property of the returned HtmlPage object
    is the url of the final page redirected to.

    If the encoding of the page is known, it can be passed as a keyword argument. If
    unspecified, the encoding is guessed using `w3lib.encoding.html_to_unicode`.
    `default_encoding` is used if the encoding cannot be determined.
    """
    fh = urlopen(url)
    info = fh.info()
    body_str = fh.read()
    # guess content encoding if not specified
    if encoding is None:
        try:
            # Python 3.x
            content_type_header = fh.getheader("content-type")
        except AttributeError:
            # Python 2.x
            content_type_header = info.getheader("content-type")
        encoding, body = html_to_unicode(content_type_header, body_str,
                default_encoding=default_encoding)
    else:
        body = body_str.decode(encoding)
    return HtmlPage(fh.geturl(), headers=dict(info.items()), body=body, encoding=encoding)


def dict_to_page(jsonpage, body_key='body'):
    """Create an HtmlPage object from a dict object.

    `body_key` is the key where the page body can be found. This is used
    sometimes when we want to store multiple version of the body (annotated and
    original) into the same dict
    """
    url = jsonpage['url']
    headers = jsonpage.get('headers')
    body = jsonpage[body_key]
    page_id = jsonpage.get('page_id')
    encoding = jsonpage.get('encoding', 'utf-8')
    return HtmlPage(url, headers, body, page_id, encoding)


def page_to_dict(page, body_key='body'):
    """Create a dict from the given HtmlPage

    `body_key` indicates what key to store the body into. See `dict_to_page`
    for more info.
    """
    return {
        'url': page.url,
        'headers': page.headers,
        body_key: page.body,
        'page_id': page.page_id,
        'encoding': page.encoding,
    }


class HtmlPage(object):
    """HtmlPage

    This is a parsed HTML page. It contains the page headers, url, raw body and parsed
    body.

    The parsed body is a list of HtmlDataFragment objects.

    The encoding argument is the original page encoding. This isn't used by the
    core extraction code, but it may be used by some extractors to translate
    entities or encoding urls.
    """
    def __init__(self, url=None, headers=None, body=None, page_id=None, encoding='utf-8'):
        assert isinstance(body, six.text_type), "unicode expected, got: %s" % type(body).__name__
        self.headers = headers or {}
        self.body = body
        self.url = url or u''
        self.encoding = encoding
        if page_id is None and url:
            self.page_id = hashlib.sha1(url.encode(self.encoding)).hexdigest()
        else:
            self.page_id = page_id

    def _set_body(self, body):
        self._body = body
        self.parsed_body = list(parse_html(body))

    body = property(lambda x: x._body, _set_body, doc="raw html for the page")

    def subregion(self, start=0, end=None):
        """HtmlPageRegion constructed from the start and end index (inclusive)
        into the parsed page
        """
        return HtmlPageParsedRegion(self, start, end)

    def fragment_data(self, data_fragment):
        """portion of the body corresponding to the HtmlDataFragment"""
        return self.body[data_fragment.start:data_fragment.end]


class TextPage(HtmlPage):
    """An HtmlPage with one unique HtmlDataFragment, needed to have a
    convenient text with same interface as html page but avoiding unnecesary
    reparsing"""
    def _set_body(self, text):
        self._body = text
        self.parsed_body = [HtmlDataFragment(0, len(self._body), True)]
    body = property(lambda x: x._body, _set_body, doc="raw text for the page")


class HtmlPageRegion(six.text_type):
    """A Region of an HtmlPage that has been extracted
    """
    def __new__(cls, htmlpage, data):
        return six.text_type.__new__(cls, data)

    def __init__(self, htmlpage, data):
        """Construct a new HtmlPageRegion object.

        htmlpage is the original page and data is the raw html
        """
        self.htmlpage = htmlpage

    @property
    def text_content(self):
        return self


class HtmlPageParsedRegion(HtmlPageRegion):
    """A region of an HtmlPage that has been extracted

    This has a parsed_fragments property that contains the parsed html
    fragments contained within this region
    """
    def __new__(cls, htmlpage, start_index, end_index):
        text = htmlpage.body
        if text:
            text_start = htmlpage.parsed_body[start_index].start
            text_end = htmlpage.parsed_body[end_index or -1].end
            text = htmlpage.body[text_start:text_end]
        return HtmlPageRegion.__new__(cls, htmlpage, text)

    def __init__(self, htmlpage, start_index, end_index):
        self.htmlpage = htmlpage
        self.start_index = start_index
        self.end_index = end_index

    def __copy__(self, page=None):
        page = page or self.htmlpage
        obj = HtmlPageParsedRegion.__new__(HtmlPageParsedRegion, page, self.start_index, self.end_index)
        HtmlPageParsedRegion.__init__(obj, page, self.start_index, self.end_index)
        return obj

    def __deepcopy__(self, memo):
        page = deepcopy(self.htmlpage)
        return self.__copy__(page)

    @property
    def parsed_fragments(self):
        """HtmlDataFragment or HtmlTag objects for this parsed region"""
        end = self.end_index + 1 if self.end_index is not None else None
        return self.htmlpage.parsed_body[self.start_index:end]

    @property
    def text_content(self):
        """Text content of this parsed region"""
        text_all = u" ".join(self.htmlpage.body[_element.start:_element.end] \
                for _element in self.parsed_fragments if \
                not isinstance(_element, HtmlTag) and _element.is_text_content)
        return TextPage(self.htmlpage.url, self.htmlpage.headers, \
                text_all, encoding=self.htmlpage.encoding).subregion()
