from cpython.version cimport PY_MAJOR_VERSION
import re

_ATTR = "((?:[^=/<>\s]|/(?!>))+)(?:\s*=(?:\s*\"(.*?)\"|\s*'(.*?)'|([^>\s]+))?)?"
_ATTR_REGEXP = re.compile(_ATTR, re.I | re.DOTALL)

class HtmlTagType(object):
    OPEN_TAG = 1
    CLOSE_TAG = 2
    UNPAIRED_TAG = 3


class HtmlDataFragment(object):
    __slots__ = ('start', 'end', 'is_text_content')

    def __init__(self, start, end, is_text_content=False):
        self.start = start
        self.end = end
        self.is_text_content = is_text_content

    def __str__(self):
        return "<HtmlDataFragment [%s:%s] is_text_content: %s>" % (self.start, self.end, self.is_text_content)

    def __repr__(self):
        return str(self)


class HtmlTag(HtmlDataFragment):
    __slots__ = ('tag_type', 'tag', '_attributes', '_attr_text')

    def __init__(self, tag_type, tag, attr_text, start, end):
        HtmlDataFragment.__init__(self, start, end)
        self.tag_type = tag_type
        self.tag = tag
        if isinstance(attr_text, dict):
            self._attributes = attr_text
            self._attr_text = None
        else: # defer loading attributes until necessary
            self._attributes = {}
            self._attr_text = attr_text

    @property
    def attributes(self):
        if not self._attributes and self._attr_text:
            for attr_match in _ATTR_REGEXP.findall(self._attr_text):
                name = attr_match[0].lower()
                values = [v for v in attr_match[1:] if v]
                # According to HTML spec if attribute name is repeated only the
                # first one is taken into account
                if name not in self._attributes:
                    self._attributes[name] = values[0] if values else None
        return self._attributes

    def __str__(self):
        return "<HtmlTag tag='%s' attributes={%s} type='%d' [%s:%s]>" % (self.tag, ', '.join(sorted\
                (["%s: %s" % (k, repr(v)) for k, v in self.attributes.items()])), self.tag_type, self.start, self.end)

    def __repr__(self):
        return str(self)


cdef class CommentParser:
    cdef int start
    cdef int end
    cdef int open_state, open_count
    cdef int close_state, close_count
    cdef int inside_comment

    def __init__(self):
        self.start = -1
        self.end = -1
        self.reset()

    cdef void reset(self):
        self.open_state = 1
        self.close_state = 1
        self.open_count = 0
        self.close_count = 0

    cdef int parse(self, Py_UCS4 c, int i):
        if ((self.open_state == 1 and c == u'<') or
            (self.open_state == 2 and c == u'!') or
            (self.open_state == 3 and c == u'-') or
            (self.open_state == 4 and c == u'-')):
            self.open_state += 1
        else:
            # Handle <!> comment
            if self.open_state == 3 and c == u'>':
                self.inside_comment = False
                self.reset()
                self.start, self.end = i - 2, i
                return True
            self.open_state = 1
        if self.open_state == 5:
            if self.open_count == 0:
                self.start = i - 3
            self.open_state = 1
            self.open_count = 1
            self.inside_comment = True

        if self.close_count < self.open_count:
            if self.close_state == 1:
                if c == u'-':
                    self.close_state += 1
            elif self.close_state == 2:
                if c == u'-':
                    self.close_state += 1
                else:
                    self.close_state = 1
            elif self.close_state == 3:
                if c == u'!':
                    self.close_state = 4
                elif c == u'>':
                    self.close_state = 5
                else:
                    self.close_state = 1
            elif self.close_state == 4:
                if c == u'>':
                    self.close_state = 5
                else:
                    self.close_state = 1

            if self.close_state == 5:
                self.close_state = 1
                self.close_count += 1
                if self.close_count >= self.open_count:
                    self.end = i
                    self.reset()
                    self.inside_comment = False
                    return True
        return False


cdef class ScriptParser:
    cdef int start
    cdef int end
    cdef int state

    def __init__(self):
        self.start = -1
        self.end = -1
        self.state = 1

    cdef int parse(self, Py_UCS4 c, int i):
        if self.state == 10:
            self.state = 1
        if ((self.state == 1 and c == u'<') or
            (self.state == 2 and c == u'/') or
            (self.state == 3 and c in u'sS') or
            (self.state == 4 and c in u'cC') or
            (self.state == 5 and c in u'rR') or
            (self.state == 6 and c in u'iI') or
            (self.state == 7 and c in u'pP') or
            (self.state == 8 and c in u'tT') or
            (self.state == 9 and c == u'>')):
            self.state += 1
        else:
            self.state = 1

        if self.state == 2:
            self.start = i
        elif self.state == 10:
            self.end = i

        return self.state == 10


# directly copied from cython's docs
cdef unicode _ustring(s):
    if type(s) is unicode:
        # fast path for most common case(s)
        return <unicode>s
    elif PY_MAJOR_VERSION < 3 and isinstance(s, bytes):
        # only accept byte strings in Python 2.x, not in Py3
        return (<bytes>s).decode('ascii')
    elif isinstance(s, unicode):
        # an evil cast to <unicode> might work here in some(!) cases,
        # depending on what the further processing does.  to be safe,
        # we can always create a copy instead
        return unicode(s)
    else:
        raise TypeError('unicode or str expected')


cpdef parse_html(s):
    cdef int OPEN_TAG = HtmlTagType.OPEN_TAG
    cdef int CLOSE_TAG = HtmlTagType.CLOSE_TAG
    cdef int UNPAIRED_TAG = HtmlTagType.UNPAIRED_TAG

    cdef unicode text = _ustring(s)

    parsed = []
    comment_parser = CommentParser()
    script_parser = ScriptParser()

    cdef int tag_end = -1         # end position of previous tag
    cdef int tag_start = -1       # start of current tag
    cdef int script = False       # True if inside script body
    cdef int open_tag = False     # True if an open tag symbol has been read
    cdef int quote_single = False # True if unpaired single quote
    cdef int quote_double = False # True if unpaired double quote
    cdef int quoted

    cdef int reset_tag = True
    cdef int slash
    cdef int has_attributes
    cdef int yield_tag

    cdef unicode tag_name
    cdef unicode tag_attributes
    cdef Py_UCS4 curr_char
    cdef Py_UCS4 prev_char = 0 # previous value of curr_char
    cdef int i = 0
    for curr_char in text:
        if reset_tag:
            reset_tag = False
            slash = False
            has_attributes = False
            tag_name = u''
            tag_attributes = u''
            yield_tag = False

        if open_tag or script:
            if curr_char == u'"' and not quote_single:
                quote_double = not quote_double
            if curr_char == u"'" and not quote_double:
                quote_single = not quote_single
        else:
            quote_single = quote_double = False
        quoted = quote_double or quote_single

        if not quoted:
            if comment_parser.parse(curr_char, i):
                if (tag_end + 1) < comment_parser.start:
                    parsed.append(
                        HtmlDataFragment(tag_end + 1, comment_parser.start, not script))
                tag_end = comment_parser.end
                parsed.append(
                    HtmlDataFragment(comment_parser.start, tag_end + 1, False))
                reset_tag = True
                if (comment_parser.end - comment_parser.start) == 2:
                    open_tag = False

        if comment_parser.inside_comment:
            open_tag = False
        else:
            if script:
                open_tag = False
                if script_parser.parse(curr_char, i):
                    script = False
                    if (tag_end + 1) < script_parser.start:
                        parsed.append(
                            HtmlDataFragment(tag_end + 1, script_parser.start, False))
                    tag_end = script_parser.end
                    parsed.append(
                        HtmlTag(CLOSE_TAG,
                                u'script', u'', script_parser.start, tag_end + 1))
            elif open_tag:
                if quoted:
                    if has_attributes:
                        tag_attributes += curr_char
                elif curr_char == u'<':
                    tag_end = i - 1
                    yield_tag = True
                elif curr_char == u'>':
                    if prev_char == u'/':
                        slash = True
                    tag_end = i
                    yield_tag = True
                    open_tag = False
                elif curr_char == u'/':
                    if prev_char == u'<':
                        slash = True
                elif curr_char.isspace():
                    if has_attributes:
                        if prev_char == u'/':
                            # feature, bug? Maintain compatilibity with previous
                            # implementation
                            tag_attributes += u'/'
                        tag_attributes += curr_char
                    elif tag_name:
                        has_attributes = True
                else:
                    if has_attributes:
                        tag_attributes += curr_char
                    else:
                        tag_name += curr_char.lower()
                if yield_tag:
                    if not slash:
                        tag_type = OPEN_TAG
                    elif prev_char != u'/':
                        tag_type = CLOSE_TAG
                    else:
                        tag_type = UNPAIRED_TAG
                    if tag_name != u'!doctype':
                        parsed.append(
                            HtmlTag(tag_type, tag_name,
                                    tag_attributes, tag_start, tag_end + 1))
                    if tag_name == u'script':
                        script = True
                    if open_tag:
                        tag_start = i
                    reset_tag = True
            else:
                open_tag = False
                if curr_char == u'<' and not quoted:
                    open_tag = True
                    tag_start = i
                    if tag_start > tag_end + 1:
                        parsed.append(
                            HtmlDataFragment(tag_end + 1, tag_start, True))
                    tag_end = tag_start
        prev_char = curr_char
        i += 1

    if tag_end + 1 < len(text):
        parsed.append(HtmlDataFragment(tag_end + 1, len(text), True))
    return parsed
