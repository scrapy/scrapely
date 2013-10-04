from __future__ import with_statement
import sys, os, re, cmd, shlex, json, optparse, json, urllib, pprint
from cStringIO import StringIO

from scrapely.htmlpage import HtmlPage, page_to_dict, url_to_page
from scrapely.template import TemplateMaker, best_match
from scrapely.extraction import InstanceBasedLearningExtractor

class IblTool(cmd.Cmd):

    prompt = 'scrapely> '

    def __init__(self, filename, **kw):
        self.filename = filename
        cmd.Cmd.__init__(self, **kw)

    def do_ta(self, line):
        """ta <url> [--encoding ENCODING] - add template"""
        opts, (url,) = parse_at(line)
        t = url_to_page(url, opts.encoding)
        templates = self._load_templates()
        templates.append(t)
        self._save_templates(templates)
        print "[%d] %s" % (len(templates) - 1, t.url)

    def do_tl(self, line):
        """tl - list templates"""
        templates = self._load_templates()
        for n, t in enumerate(templates):
            print "[%d] %s" % (n, t.url)

    def do_td(self, template_id):
        """dt <template> - delete template"""
        templates = self._load_templates()
        try:
            del templates[int(template_id)]
            self._save_templates(templates)
            print "template deleted: %s" % template_id
        except IndexError:
            print "template not found: %s" % template_id

    def do_t(self, line):
        """t <template> <text> - test selection text"""
        template_id, criteria = line.split(' ', 1)
        t = self._load_template(template_id)
        criteria = self._parse_criteria(criteria)
        tm = TemplateMaker(t)
        selection = apply_criteria(criteria, tm)
        for n, i in enumerate(selection):
            print "[%d] %r" % (n, remove_annotation(tm.selected_data(i)))

    def do_a(self, line):
        """a <template> <data> [-n number] [-f field]- add or test annotation

        Add a new annotation (if -f is passed) or test what would be annotated
        otherwise
        """
        template_id, criteria = line.split(' ', 1)
        t = self._load_template(template_id)
        criteria = self._parse_criteria(criteria)
        tm = TemplateMaker(t)
        selection = apply_criteria(criteria, tm)
        if criteria.field:
            for index in selection:
                index = selection[0]
                tm.annotate_fragment(index, criteria.field)
                self._save_template(template_id, tm.get_template())
                print "[new] (%s) %r" % (criteria.field,
                    remove_annotation(tm.selected_data(index)))
        else:
            for n, i in enumerate(selection):
                print "[%d] %r" % (n, remove_annotation(tm.selected_data(i)))

    def do_al(self, template_id):
        """al <template> - list annotations"""
        if assert_or_print(template_id, "missing template id"):
            return
        t = self._load_template(template_id)
        tm = TemplateMaker(t)
        for n, (a, i) in enumerate(tm.annotations()):
            print "[%s-%d] (%s) %r" % (template_id, n, a['annotations']['content'],
                remove_annotation(tm.selected_data(i)))

    def do_s(self, url):
        """s <url> - scrape url"""
        templates = self._load_templates()
        if assert_or_print(templates, "no templates available"):
            return
        # fall back to the template encoding if none is specified
        page = url_to_page(url, default_encoding=templates[0].encoding)
        ex = InstanceBasedLearningExtractor((t, None) for t in templates)
        pprint.pprint(ex.extract(page)[0])

    def default(self, line):
        if line == 'EOF':
            if self.use_rawinput:
                print
            return True
        elif line:
            return cmd.Cmd.default(self, line)

    def _load_annotations(self, template_id):
        t = self._load_template(template_id)
        tm = TemplateMaker(t)
        return [x[0] for x in tm.annotations()]

    def _load_template(self, template_id):
        templates = self._load_templates()
        return templates[int(template_id)]

    def _load_templates(self):
        if not os.path.exists(self.filename):
            return []
        with open(self.filename) as f:
            templates = json.load(f)['templates']
            templates = [HtmlPage(t['url'], body=t['body'], encoding=t['encoding']) \
                for t in templates]
            return templates

    def _save_template(self, template_id, template):
        templates = self._load_templates()
        templates[int(template_id)] = template
        self._save_templates(templates)

    def _save_templates(self, templates):
        with open(self.filename, 'w') as f:
            templates = [page_to_dict(t) for t in templates]
            return json.dump({'templates': templates}, f)

    def _parse_criteria(self, criteria_str):
        """Parse the given criteria string and returns a criteria object"""
        p = optparse.OptionParser()
        p.add_option('-f', '--field', help='field to annotate')
        p.add_option('-n', '--number', type="int", help='number of result to select')
        o, a = p.parse_args(shlex.split(criteria_str))

        encoding = getattr(self.stdin, 'encoding', None) or sys.stdin.encoding
        o.text = ' '.join(a).decode(encoding or 'ascii')
        return o


def parse_at(ta_line):
    p = optparse.OptionParser()
    p.add_option('-e', '--encoding', help='page encoding')
    return p.parse_args(shlex.split(ta_line))

def apply_criteria(criteria, tm):
    """Apply the given criteria object to the given template"""
    func = best_match(criteria.text) if criteria.text else lambda x, y: False
    sel = tm.select(func)
    if criteria.number is not None:
        if criteria.number < len(sel):
            sel = [sel[criteria.number]]
        else:
            sel = []
    return sel

def remove_annotation(text):
    return re.sub(u' ?data-scrapy-annotate=".*?"', '', text)

def assert_or_print(condition, text):
    if not condition:
        sys.stderr.write(text + os.linesep)
        return True

def args_to_file(args):
    s = []
    for a in args:
        if ' ' in a:
            if '"' in a:
                a = "'%s'" % a
            else:
                a = '"%s"' % a
        s.append(a)
    return StringIO(' '.join(s))

def main():
    if len(sys.argv) == 1:
        print "usage: %s <scraper_file> [command arg ...]" % sys.argv[0]
        sys.exit(2)

    filename, args = sys.argv[1], sys.argv[2:]
    if args:
        t = IblTool(filename, stdin=args_to_file(args))
        t.prompt = ''
        t.use_rawinput = False
    else:
        t = IblTool(filename)
    t.cmdloop()

if __name__ == '__main__':
    main()
