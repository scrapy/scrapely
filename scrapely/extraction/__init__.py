"""
IBL module

This contains an extraction algorithm based on the paper Extracting Web Data
Using Instance-Based Learning by Yanhong Zhai and Bing Liu.

It defines the InstanceBasedLearningExtractor class, which implements this
extraction algorithm.

Main departures from the original algorithm:
    * there is no limit in prefix or suffix size
    * we have "attribute adaptors" that allow generic post processing and may
      affect the extraction process. For example, a price field may require a
      numeric value to be present.
    * tags can be inserted to extract regions not wrapped by html tags. These
      regions are then identified using the longest unique character prefix and
      suffix.
"""
from operator import itemgetter
from .pageparsing import parse_template, parse_extraction_page
from .pageobjects import TokenDict
from .regionextract import (BasicTypeExtractor, TraceExtractor, RepeatedDataExtractor,
                            AdjacentVariantExtractor, RecordExtractor, TemplatePageExtractor)


class InstanceBasedLearningExtractor(object):
    """Implementation of the instance based learning algorithm to
    extract data from web pages.
    """
    _extractor_classes = [
        RepeatedDataExtractor,
        AdjacentVariantExtractor,
        RepeatedDataExtractor,
        AdjacentVariantExtractor,
        RepeatedDataExtractor,
        RecordExtractor,
    ]

    def __init__(self, td_pairs, trace=False, apply_extrarequired=True):
        """Initialise this extractor

        td_pairs is a list of (template, item descriptor) pairs.

        templates should contain a sequence of strings, each containing
        annotated html that will be used as templates for extraction.

        Tags surrounding areas to be extracted must contain a
        'data-scrapy-annotate' attribute and the value must be the name
        of the attribute. If the tag was inserted and was not present in the
        original page, the data-scrapy-generated attribute must be present.

        item descriptors describe how the item will be extracted from target
        page, using the corresponding template.

        if trace is true, the returned extracted data will have a 'trace'
        property that contains a trace of the extraction execution.
        """
        self.token_dict = TokenDict()
        parsed_plus_tdpairs = [(parse_template(self.token_dict, td[0]), td) for td in td_pairs]
        parsed_plus_epages = (
            (p, parse_extraction_page(self.token_dict, td[0]), td)
            for p, td in parsed_plus_tdpairs if _annotation_count(p)
        )
        parsed_tdpairs = map(itemgetter(0, 2), parsed_plus_epages)

        modified_parsed_tdpairs = []
        # apply extra required attributes
        for parsed, (t, descriptor) in parsed_tdpairs:
            if descriptor is not None and apply_extrarequired:
                descriptor = descriptor.copy()
                for attr in parsed.extra_required_attrs:
                    descriptor._required_attributes.append(attr)
                    # not always is present a descriptor for a given attribute
                    if attr in descriptor.attribute_map:
                        # not strictly necesary, but avoid possible inconsistences for user
                        descriptor.attribute_map[attr].required = True
            modified_parsed_tdpairs.append((parsed, (t, descriptor)))
        # templates with more attributes are considered first
        sorted_tdpairs = sorted(modified_parsed_tdpairs,
                key=lambda x: _annotation_count(x[0]), reverse=True)
        self.extraction_trees = [
            self.build_extraction_tree(p, td[1], trace)
            for p, td in sorted_tdpairs
        ]
        self.validated = dict(
            (td[0].page_id, td[1].validated if td[1] else self._filter_not_none)
            for _, td in sorted_tdpairs
        )

    def build_extraction_tree(self, template, type_descriptor, trace=True):
        """Build a tree of region extractors corresponding to the
        template
        """
        attribute_map = type_descriptor.attribute_map if type_descriptor else None
        extractors = BasicTypeExtractor.create(template.annotations, attribute_map)
        if trace:
            extractors = TraceExtractor.apply(template, extractors)
        for cls in self._extractor_classes:
            extractors = cls.apply(template, extractors)
            if trace:
                extractors = TraceExtractor.apply(template, extractors)

        return TemplatePageExtractor(template, extractors)

    def extract(self, html, pref_template_id=None):
        """extract data from an html page

        If pref_template_url is specified, the template with that url will be
        used first.
        """
        extraction_page = parse_extraction_page(self.token_dict, html)
        if pref_template_id is not None:
            extraction_trees = sorted(self.extraction_trees,
                    key=lambda x: x.template.id != pref_template_id)
        else:
            extraction_trees = self.extraction_trees

        for extraction_tree in extraction_trees:
            extracted = extraction_tree.extract(extraction_page)
            correctly_extracted = self.validated[extraction_tree.template.id](extracted)
            if len(correctly_extracted) > 0:
                return correctly_extracted, extraction_tree.template
        return None, None

    def __str__(self):
        return "InstanceBasedLearningExtractor[\n%s\n]" % \
                (',\n'.join(map(str, self.extraction_trees)))

    @staticmethod
    def _filter_not_none(items):
        return [d for d in items if d is not None]


def _annotation_count(template):
    return len(template.annotations)
