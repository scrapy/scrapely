"""More complex tests with elaborated tolls like used in slybot"""
import re

from scrapely.extractors import htmlregion
from scrapely.tests.utils import _TestIblBase
from scrapely.extractors import text
from scrapely.descriptor import (FieldDescriptor as A, 
        ItemDescriptor)

# ------ CODE COPIED FROM SLYBOT FOR USAGE IN TESTS ----------

def create_regex_extractor(pattern):
    """Create extractor from a regular expression.
    Only groups from match are extracted and concatenated, so it
    is required to define at least one group. Ex:
    >>> extractor = create_regex_extractor("(\d+).*(\.\d+)")
    >>> extractor(u"The price of this product is <div>45</div> </div class='small'>.50</div> pounds")
    u'45.50'
    """
    ereg = re.compile(pattern, re.S)
    def _extractor(txt):
        m = ereg.search(txt)
        if m:
            return htmlregion(u"".join(filter(None, m.groups() or m.group())))
    
    _extractor.__name__ = "Regex: %s" % pattern.encode("utf-8")
    return _extractor

class PipelineExtractor:
    def __init__(self, *extractors):
        self.extractors = extractors
    
    def __call__(self, value):
        for extractor in self.extractors:
            value = extractor(value) if value else value
        return value

    @property                                                                                                                                
    def __name__(self):
        return repr(self.extractors)

extract_text = lambda r: text(r.text_content)
extract_raw = lambda r: r

# -------- FINISHED CODE COPIED FROM SLYBOT ------------------

ANNOTATED_PAGE1 = u"""
<table><h2 data-scrapy-annotate="{&quot;required&quot;: [&quot;_sticky1&quot;], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;_sticky1&quot;}}">About me</h2>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;gender&quot;}}"><th class="item-key">Gender</th>
<td>Male</td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;industry&quot;}}"><th class="item-key">Industry</th>
<td><span class="role"><a href="/profile-find.g?t=j&amp;ind=MUSEUMS_OR_LIBRARIES">Museums or Libraries</a></span></td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;occupation&quot;}}"><th class="item-key">Occupation</th>
<td><span class="title"><a href="/profile-find.g?t=o&amp;q=Glass+Cleaner">Glass Cleaner</a></span></td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;location&quot;}, &quot;generated&quot;: false}"><th class="item-key">Location</th>
<td><span class="locality"><a href="/profile-find.g?t=l&amp;loc0=US&amp;loc1=MI&amp;loc2=Clarkston">Clarkston</a>,</span>
<span class="region"><a href="/profile-find.g?t=l&amp;loc0=US&amp;loc1=MI">MI</a>,</span>
<span class="country-name"><a href="/profile-find.g?t=l&amp;loc0=US">United States</a></span></td></tr>

<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;introduction&quot;}}"><th class="item-key">Introduction</th>
<td>Wow this is cool.</td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;interests&quot;}}"><th class="item-key">Interests</th>
<td><span class="favorites"><a href="/profile-find.g?t=i&amp;q=Diving">Diving,</a> <a href="/profile-find.g?t=i&amp;q=Running">Running,</a> <a href="/profile-find.g?t=i&amp;q=Sitting">Sitting</a></span></td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;favorite_movies&quot;}}"><th class="item-key">Favorite Movies</th>
<td><span class="favorites"><a href="/profile-find.g?t=m&amp;q=Batman">Batman,</a> <a href="/profile-find.g?t=m&amp;q=Superman">Superman,</a> <a href="/profile-find.g?t=m&amp;q=Wonderman">Wonderman</a></span></td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;favorite_music&quot;}}"><th class="item-key">Favorite Music</th>
<td><span class="favorites"><a href="/profile-find.g?t=s&amp;q=Loud">Loud</a></span></td></tr>
<tr data-scrapy-annotate="{&quot;required&quot;: [], &quot;variant&quot;: 0, &quot;annotations&quot;: {&quot;content&quot;: &quot;favorite_books&quot;}}"><th class="item-key">Favorite Books</th>
<td><span class="favorites"><a href="/profile-find.g?t=b&amp;q=See+Doppy+Run">See Doppy Run</a></span></td></tr></table>
</div></div>
<div id="footer"><a href="/go/helpcenter">Help Center</a>
<span class="spacer">|</span>
<a href="/go/terms">Terms of Service</a>
<span class="spacer">|</span>
<a href="/go/privacy">Privacy</a>
<span class="spacer">|</span>
<a href="/go/contentpolicy">Content Policy</a>
<span class="spacer">|</span>
<a href="/go/developers">Developers</a>
"""

EXTRACT_PAGE1a = u"""
<table><h2>About me</h2>
<tr><th class="item-key">Gender</th>
<td>Male</td></tr>
<tr><th class="item-key">Industry</th>
<td><span class="role"><a href="/profile-find.g?t=j&amp;ind=BIOTECH">Biotech</a></span></td></tr>
<tr><th class="item-key">Occupation</th>
<td><span class="title"><a href="/profile-find.g?t=o&amp;q=Biochemistry">Biochemistry</a></span></td></tr>
<tr><th class="item-key">Location</th>
<td>

<span class="country-name"><a href="/profile-find.g?t=l&amp;loc0=CH">Switzerland</a></span></td></tr>

<tr><th class="item-key">Introduction</th>
<td>I'm cool!!</td></tr>
<tr><th class="item-key">Interests</th>
<td><span class="favorites"><a href="/profile-find.g?t=i&amp;q=Biochemistry">Biochemistry</a></span></td></tr>
<tr><th class="item-key">Favourite Films</th>
<td><span class="favorites"><a href="/profile-find.g?t=m&amp;q=Tonari+no+Totoro">Tonari no Totoro</a></span></td></tr>
<tr><th class="item-key">Favourite Music</th>
<td><span class="favorites"><a href="/profile-find.g?t=s&amp;q=Abba">Abba</a></span></td></tr>
</table>
</div></div>
<div id="footer"><a href="/go/helpcenter">Help Centre</a>
<span class="spacer">|</span>
<a href="/go/terms">Terms of Service</a>
<span class="spacer">|</span>
<a href="/go/privacy">Privacy</a>
<span class="spacer">|</span>
<a href="/go/contentpolicy">Content Policy</a>
<span class="spacer">|</span>
<a href="/go/developers">Developers</a>
"""

SAMPLE_DESCRIPTOR1 = ItemDescriptor('sample31', 'descriptor for extractor helped extraction', [
        A('_sticky', '', PipelineExtractor(extract_text, create_regex_extractor('About\s+me'))),
        A('gender', '', PipelineExtractor(extract_text, create_regex_extractor('Gender\s+(Male|Female)'))),
        A('industry', '', PipelineExtractor(extract_text, create_regex_extractor('Industry\s+(.+)'))),
        A('occupation', '', PipelineExtractor(extract_text, create_regex_extractor('Occupation\s+(.+)'))),
        A('location', '', PipelineExtractor(extract_text, create_regex_extractor('Location\s+(.+)'))),
        A('introduction', '', PipelineExtractor(extract_text, create_regex_extractor('Introduction\s+(.+)'))),
        A('interests', '', PipelineExtractor(extract_text, create_regex_extractor('Interests\s+(.+)'))),
        A('favorite_movies', '', PipelineExtractor(extract_text, create_regex_extractor('Favou?rite\s+(?:Movies|Films)\s+(.+)'))),
        A('favorite_music', '', PipelineExtractor(extract_text, create_regex_extractor('Favou?rite\s+Music\s+(.+)'))),
        A('favorite_books', '', PipelineExtractor(extract_text, create_regex_extractor('Favou?rite\s+Books\s+(.+)'))),
        ]
    )

TEST_DATA = [
    ('extract all fields of a variable row table from a template with all possible fields, using extractors as matching help',
        [ANNOTATED_PAGE1], EXTRACT_PAGE1a, SAMPLE_DESCRIPTOR1,
        {
            u'interests': [u'Biochemistry'],
            u'favorite_movies': [u'Tonari no Totoro'],
            u'introduction': [u"I'm cool!!"],
            u'gender': [u'Male'],
            u'industry': [u'Biotech'],
            u'location': [u'Switzerland'],
            u'_sticky1': [u'About me'],
            u'favorite_music': [u'Abba'],
            u'occupation': [u'Biochemistry']
        }
    ),

]
class TestIblII(_TestIblBase):
    TESTCASE_DATA = TEST_DATA

