import sys
import os
import shutil
from collections import namedtuple
from lxml import etree
from xml.dom.minidom import parse
from xml.dom import Node

from skoolkittest import SkoolKitTestCase, SKOOLKIT_HOME

sys.path.insert(0, SKOOLKIT_HOME)
from skoolkit.skoolhtml import HtmlWriter
from skoolkit.skoolmacro import get_macros

class MacroExpander(HtmlWriter):
    def __init__(self, base, case):
        self.parser = namedtuple('SkoolParser', ('base', 'case'))(base, case)
        self.macros = get_macros(self)

def _find_ids_and_hrefs(elements, doc_anchors, doc_hrefs):
    for node in elements:
        if node.nodeType == Node.ELEMENT_NODE:
            element_id = node.getAttribute('id')
            if element_id:
                doc_anchors.add(element_id)
            if node.tagName in ('a', 'link', 'img', 'script'):
                if node.tagName == 'a':
                    element_name = node.getAttribute('name')
                    if element_name:
                        doc_anchors.add(element_name)
                if node.tagName in ('a', 'link'):
                    element_href = node.getAttribute('href')
                    if element_href:
                        doc_hrefs.add(element_href)
                elif node.tagName in ('img', 'script'):
                    element_src = node.getAttribute('src')
                    if element_src:
                        doc_hrefs.add(element_src)
            _find_ids_and_hrefs(node.childNodes, doc_anchors, doc_hrefs)

def _read_files(root_dir):
    all_files = {} # filename -> (element ids and <a> names, hrefs and srcs)
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d != '.git']
        for f in files:
            if f != '.gitlab-ci.yml':
                fname = os.path.join(root, f)
                all_files[fname] = (set(), set())
                if f.endswith('.html'):
                    doc = parse(fname)
                    _find_ids_and_hrefs(doc.documentElement.childNodes, *all_files[fname])
    return all_files

def check_links(root_dir):
    missing_files = []
    missing_anchors = []
    all_files = _read_files(root_dir)
    linked = set()
    for fname in all_files:
        for href in all_files[fname][1]:
            if not href.startswith('http://'):
                if href.startswith('#'):
                    link_dest = fname + href
                else:
                    link_dest = os.path.normpath(os.path.join(os.path.dirname(fname), href))
                dest_fname, sep, anchor = link_dest.partition('#')
                linked.add(dest_fname)
                if dest_fname not in all_files:
                    missing_files.append((fname, link_dest))
                elif anchor and anchor not in all_files[dest_fname][0]:
                    missing_anchors.append((fname, link_dest))
    orphans = set()
    for fname in all_files:
        if fname not in linked:
            orphans.add(fname)
    return all_files, orphans, missing_files, missing_anchors

class DisassembliesTestCase(SkoolKitTestCase):
    def _write_skool(self, snapshot, ctl):
        if not os.path.isfile(snapshot):
            self.fail("{} not found".format(snapshot))
        os.environ['SKOOLKIT_HOME'] = SKOOLKIT_HOME
        options = '-c {}'.format(ctl)
        output, error = self.run_sna2skool('{} {}'.format(options, snapshot), out_lines=False, err_lines=True)
        self.assertEqual(['Using control file: {}'.format(ctl)], error)
        return self.write_text_file(output)

class AsmTestCase(DisassembliesTestCase):
    def _test_asm(self, options, skool=None, snapshot=None, ctl=None, clean=True):
        if not skool:
            skool = self._write_skool(snapshot, ctl)
        output, stderr = self.run_skool2asm('{} {}'.format(options, skool))
        stderr = [line.rstrip() for line in stderr.split('\n')][:-1]
        if clean:
            self.assertTrue(stderr[0].startswith('Parsed {}'.format(skool)))
            self.assertIn(len(stderr), (2, 3))
        else:
            self.assertTrue(any([line.startswith('Parsed {}'.format(skool)) for line in stderr]))
        self.assertTrue(stderr[-1].startswith('Wrote ASM to stdout'))

class CtlTestCase(DisassembliesTestCase):
    def _test_ctl(self, options, skool=None, snapshot=None, ctl=None):
        if not skool:
            skool = self._write_skool(snapshot, ctl)
        args = '{} {}'.format(options, skool)
        output, stderr = self.run_skool2ctl(args)
        self.assertEqual(stderr, '')

class HtmlTestCase(DisassembliesTestCase):
    def setUp(self):
        DisassembliesTestCase.setUp(self)
        self.odir = 'html-{0}'.format(os.getpid())
        self.tempdirs.append(self.odir)

    def _validate_xhtml(self):
        for root, dirs, files in os.walk(self.odir):
            for fname in files:
                if fname.endswith('.html'):
                    htmlfile = os.path.join(root, fname)
                    try:
                        etree.parse(htmlfile)
                    except etree.LxmlError as e:
                        self.fail('Error while parsing {}: {}'.format(htmlfile, e.message))

    def _check_links(self):
        all_files, orphans, missing_files, missing_anchors = check_links(self.odir)
        if orphans or missing_files or missing_anchors:
            error_msg = []
            if orphans:
                error_msg.append('Orphaned files: {}'.format(len(orphans)))
                for fname in orphans:
                    error_msg.append('  {}'.format(fname))
            if missing_files:
                error_msg.append('Links to non-existent files: {}'.format(len(missing_files)))
                for fname, link_dest in missing_files:
                    error_msg.append('  {} -> {}'.format(fname, link_dest))
            if missing_anchors:
                error_msg.append('Links to non-existent anchors: {}'.format(len(missing_anchors)))
                for fname, link_dest in missing_anchors:
                    error_msg.append('  {} -> {}'.format(fname, link_dest))
            self.fail('\n'.join(error_msg))

    def _test_html(self, options, skool=None, snapshot=None, ctl=None, output=None, ref=None):
        base = case = None
        if '-H' in options:
            base = 16
        elif '-D' in options:
            base = 10
        if '-l' in options:
            case = 1
        elif '-u' in options:
            case = 2
        macro_expander = MacroExpander(base, case)
        if not skool:
            skool = self._write_skool(snapshot, ctl)
            options += ' -c Config/SkoolFile={}'.format(skool)
        if not ref:
            ref = skool[:-5] + 'ref'
        shutil.rmtree(self.odir, True)
        stdout, error = self.run_skool2html('-d {} {} {}'.format(self.odir, options, ref))
        self.assertEqual(error, '')
        reps = {'odir': self.odir, 'SKOOLKIT_HOME': SKOOLKIT_HOME, 'skoolfile': skool, 'reffile': ref}
        exp_output = macro_expander.expand(output.format(**reps)).split('\n')
        self.assertEqual(exp_output, stdout)
        self._validate_xhtml()
        self._check_links()

class SftTestCase(DisassembliesTestCase):
    def _test_sft(self, options, skool=None, snapshot=None, sna2skool_opts=None, ctl=None):
        if not skool:
            skool = self._write_skool(snapshot, ctl)
        with open(skool) as f:
            orig_skool = f.read().rstrip().split('\n')
        args = '{} {}'.format(options, skool)
        sft, stderr = self.run_skool2sft(args, out_lines=False)
        self.assertEqual(stderr, '')
        sftfile = self.write_text_file(sft)
        options = '-T {}'.format(sftfile)
        if sna2skool_opts:
            options += ' {}'.format(sna2skool_opts)
        output, stderr = self.run_sna2skool('{} {}'.format(options, snapshot))
        self.assertEqual(orig_skool, output)
