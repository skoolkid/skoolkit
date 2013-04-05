# -*- coding: utf-8 -*-
import sys
import os
import shutil
from subprocess import Popen, PIPE
from lxml import etree
from xml.dom.minidom import parse
from xml.dom import Node
from nose.plugins.skip import SkipTest

from skoolkittest import SkoolKitTestCase, PY3, SKOOLKIT_HOME

MM2CTL = '{0}/utils/mm2ctl.py'.format(SKOOLKIT_HOME)
MMZ80 = '{0}/snapshots/manic_miner.z80'.format(SKOOLKIT_HOME)
JSW2CTL = '{0}/utils/jsw2ctl.py'.format(SKOOLKIT_HOME)
JSWZ80 = '{0}/snapshots/jet_set_willy.z80'.format(SKOOLKIT_HOME)

XHTML_XSD = os.path.join(SKOOLKIT_HOME, 'XSD', 'xhtml1-strict.xsd')

OUTPUT_MM = """Creating directory {odir}
Using skool file: {skoolfile}
Using ref file: ../examples/manic_miner.ref
Parsing {skoolfile}
Creating directory {odir}/manic_miner
Copying {cssfile} to {odir}/manic_miner/{cssfile}
  Wrote manic_miner/images/logo.png
  Writing disassembly files in manic_miner/asm
  Writing manic_miner/maps/all.html
  Writing manic_miner/maps/routines.html
  Writing manic_miner/maps/data.html
  Writing manic_miner/maps/messages.html
  Writing manic_miner/buffers/gbuffer.html
  Writing manic_miner/index.html"""

OUTPUT_JSW = """Creating directory {odir}
Using skool file: {skoolfile}
Using ref file: ../examples/jet_set_willy.ref
Parsing {skoolfile}
Creating directory {odir}/jet_set_willy
Copying {cssfile} to {odir}/jet_set_willy/{cssfile}
  Wrote jet_set_willy/images/logo.png
  Writing disassembly files in jet_set_willy/asm
  Writing jet_set_willy/maps/all.html
  Writing jet_set_willy/maps/routines.html
  Writing jet_set_willy/maps/data.html
  Writing jet_set_willy/maps/messages.html
  Writing jet_set_willy/maps/unused.html
  Writing jet_set_willy/buffers/gbuffer.html
  Writing jet_set_willy/reference/facts.html
  Writing jet_set_willy/index.html"""

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
        for f in files:
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

class DisassembliesTest(SkoolKitTestCase):
    def _run_cmd(self, cmd):
        cmdline = cmd.split()
        if sys.platform == 'win32':
            cmdline.insert(0, 'python')
        p = Popen(cmdline, stdout=PIPE, stderr=PIPE)
        out, err = p.communicate()
        if PY3:
            out = out.decode()
            err = err.decode()
        return out, err

    def _write_skool(self, ctlutil, snapshot, prefix):
        if not os.path.isfile(snapshot):
            raise SkipTest("{0} not found".format(snapshot))
        os.environ['SKOOLKIT_HOME'] = SKOOLKIT_HOME
        output, error = self._run_cmd('{0} {1}'.format(ctlutil, snapshot))
        self.assertEqual(len(error), 0)
        ctlfile = '{0}-{1}.ctl'.format(prefix, os.getpid())
        self.write_text_file(output, ctlfile)
        output, error = self.run_sna2skool('-c {0} {1}'.format(ctlfile, snapshot), out_lines=False)
        self.assertEqual(len(error), 0)
        skoolfile = '{0}-{1}.skool'.format(prefix, os.getpid())
        self.write_text_file(output, skoolfile)
        return skoolfile

    def _write_mm_skool(self):
        return self._write_skool(MM2CTL, MMZ80, 'manic_miner')

    def _write_jsw_skool(self):
        return self._write_skool(JSW2CTL, JSWZ80, 'jet_set_willy')

class AsmTest(DisassembliesTest):
    def _test_asm(self, skoolfile, clean=True):
        for b in ('', '-D', '-H'):
            for c in ('', '-l', '-u'):
                for f in ('', '-f 1', '-f 2', '-f 3'):
                    for p in ('', '-s', '-r'):
                        args = '{0} {1} {2} {3} {4}'.format(b, c, f, p, skoolfile)
                        fail_msg = "skool2asm.py {0} failed".format(args)
                        output, stderr = self.run_skool2asm(args, err_lines=True)
                        if clean:
                            self.assertTrue(stderr[0].startswith('Parsed {0}'.format(skoolfile)), fail_msg)
                            self.assertEqual(len(stderr), 3, fail_msg)
                        else:
                            self.assertTrue(any([line.startswith('Parsed {0}'.format(skoolfile)) for line in stderr]), fail_msg)
                        self.assertTrue(stderr[-1].startswith('Wrote ASM to stdout'), fail_msg)

    def test_mm_asm(self):
        skoolfile = self._write_skool(MM2CTL, MMZ80, 'manic_miner')
        self._test_asm(skoolfile, False)

    def test_jsw_asm(self):
        skoolfile = self._write_skool(JSW2CTL, JSWZ80, 'jet_set_willy')
        self._test_asm(skoolfile, False)

class CtlTest(DisassembliesTest):
    def _test_ctl(self, skoolfile):
        for w in ('', '-w b', '-w bt', '-w btd', '-w btdr', '-w btdrm', '-w btdrms', '-w btdrmsc'):
            for h in ('', '-h'):
                for a in ('', '-a'):
                    args = '{0} {1} {2} {3}'.format(w, h, a, skoolfile)
                    output, stderr = self.run_skool2ctl(args)
                    self.assertEqual(stderr, '')

    def test_mm_ctl(self):
        self._test_ctl(self._write_mm_skool())

    def test_jsw_ctl(self):
        self._test_ctl(self._write_jsw_skool())

class HtmlTest(DisassembliesTest):
    def setUp(self):
        DisassembliesTest.setUp(self)
        self.odir = 'html-{0}'.format(os.getpid())
        self.tempdirs.append(self.odir)

    def _test_html(self, html_dir, ref_file, exp_output, skoolfile):
        cssfile = self.write_text_file(suffix='.css')
        c_options = '-c Paths/StyleSheet={0}'.format(cssfile)
        c_options += ' -c Config/SkoolFile={0}'.format(skoolfile)
        for option in ('', '-H', '-D', '-l', '-u'):
            shutil.rmtree(self.odir, True)

            # Write the disassembly
            output, error = self.run_skool2html('{0} -d {1} {2} {3}'.format(c_options, self.odir, option, ref_file))
            self.assertEqual(len(error), 0)
            reps = {'odir': self.odir, 'cssfile': cssfile, 'skoolfile': skoolfile}
            self.assertEqual(output, exp_output.format(**reps).split('\n'))

            # Do XHTML validation using lxml.etree
            if os.path.isfile(XHTML_XSD):
                with open(XHTML_XSD) as f:
                    xmlschema_doc = etree.parse(f)
                xmlschema = etree.XMLSchema(xmlschema_doc)
                for root, dirs, files in os.walk(self.odir):
                    for fname in files:
                        if fname[-5:] == '.html':
                            htmlfile = os.path.join(root, fname)
                            try:
                                xhtml = etree.parse(htmlfile)
                            except etree.LxmlError as e:
                                self.fail('Error while parsing {0}: {1}'.format(htmlfile, e.message))
                            try:
                                xmlschema.assertValid(xhtml)
                            except etree.DocumentInvalid as e:
                                self.fail('Error while validating {0}: {1}'.format(htmlfile, e.message))

            # Check links
            all_files, orphans, missing_files, missing_anchors = check_links(self.odir)
            if orphans or missing_files or missing_anchors:
                error_msg = []
                if orphans:
                    error_msg.append('Orphaned files: {0}'.format(len(orphans)))
                    for fname in orphans:
                        error_msg.append('  {0}'.format(fname))
                if missing_files:
                    error_msg.append('Links to nonexistent files: {0}'.format(len(missing_files)))
                    for fname, link_dest in missing_files:
                        error_msg.append('  {0} -> {1}'.format(fname, link_dest))
                if missing_anchors:
                    error_msg.append('Links to nonexistent anchors: {0}'.format(len(missing_anchors)))
                    for fname, link_dest in missing_anchors:
                        error_msg.append('  {0} -> {1}'.format(fname, link_dest))
                self.fail('\n'.join(error_msg))

    def test_mm_html(self):
        self._test_html('manic_miner', '../examples/manic_miner.ref', OUTPUT_MM, self._write_mm_skool())

    def test_jsw_html(self):
        self._test_html('jet_set_willy', '../examples/jet_set_willy.ref', OUTPUT_JSW, self._write_jsw_skool())

class SftTest(DisassembliesTest):
    def _test_sft(self, skoolfile, snapshot):
        with open(skoolfile, 'rt') as f:
            orig_skool = f.read().split('\n')
        for h in ('', '-h'):
            args = '{0} {1}'.format(h, skoolfile)
            sft, stderr = self.run_skool2sft(args, out_lines=False)
            self.assertEqual(stderr, '')
            sftfile = self.write_text_file(sft)
            output, stderr = self.run_sna2skool('-T {0} {1}'.format(sftfile, snapshot))
            self.assert_output_equal(output, orig_skool[:-1])

    def test_mm_sft(self):
        self._test_sft(self._write_mm_skool(), MMZ80)

    def test_jsw_sft(self):
        self._test_sft(self._write_jsw_skool(), JSWZ80)
