# -*- coding: utf-8 -*-
import sys
import os
import shutil
from subprocess import Popen, PIPE
from lxml import etree
from xml.dom.minidom import parse
from xml.dom import Node
from nose.plugins.skip import SkipTest

from skoolkittest import SkoolKitTestCase, SKOOLKIT_HOME

PY3 = sys.version_info >= (3,)

MM2CTL = '{0}/utils/mm2ctl.py'.format(SKOOLKIT_HOME)
MMZ80 = '{0}/snapshots/manic_miner.z80'.format(SKOOLKIT_HOME)
MMREF = '{}/examples/manic_miner.ref'.format(SKOOLKIT_HOME)
ROM = '/usr/share/spectrum-roms/48.rom'
ROMCTL = '{}/examples/48.rom.ctl'.format(SKOOLKIT_HOME)
ROMREF = '{}/examples/48.rom.ref'.format(SKOOLKIT_HOME)

XHTML_XSD = os.path.join(SKOOLKIT_HOME, 'XSD', 'xhtml1-strict.xsd')

OUTPUT_MM = """Creating directory {odir}
Using skool file: {skoolfile}
Using ref file: {reffile}
Parsing {skoolfile}
Creating directory {odir}/manic_miner
Copying {cssfile} to {odir}/manic_miner/{cssfile}
  Writing disassembly files in manic_miner/asm
  Writing manic_miner/maps/all.html
  Writing manic_miner/maps/routines.html
  Writing manic_miner/maps/data.html
  Writing manic_miner/maps/messages.html
  Writing manic_miner/buffers/gbuffer.html
  Writing manic_miner/reference/changelog.html
  Writing manic_miner/index.html"""

OUTPUT_ROM = """Creating directory {odir}
Using skool file: {skoolfile}
Using ref file: {reffile}
Parsing {skoolfile}
Creating directory {odir}/rom
Copying {cssfile} to {odir}/rom/{cssfile}
  Writing disassembly files in rom/asm
  Writing rom/maps/all.html
  Writing rom/maps/routines.html
  Writing rom/maps/data.html
  Writing rom/maps/messages.html
  Writing rom/maps/unused.html
  Writing rom/reference/changelog.html
  Writing rom/index.html"""

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

class DisassembliesTestCase(SkoolKitTestCase):
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

    def _write_skool(self, snapshot, prefix, ctlutil=None, ctlfile=None, org=None):
        if not os.path.isfile(snapshot):
            raise SkipTest("{0} not found".format(snapshot))
        os.environ['SKOOLKIT_HOME'] = SKOOLKIT_HOME
        if ctlutil:
            output, error = self._run_cmd('{0} {1}'.format(ctlutil, snapshot))
            self.assertEqual(len(error), 0)
            ctlfile = '{0}-{1}.ctl'.format(prefix, os.getpid())
            self.write_text_file(output, ctlfile)
        options = '-c {}'.format(ctlfile)
        if org is not None:
            options += ' -o {}'.format(org)
        output, error = self.run_sna2skool('{} {}'.format(options, snapshot), out_lines=False)
        self.assertEqual(len(error), 0)
        skoolfile = '{0}-{1}.skool'.format(prefix, os.getpid())
        self.write_text_file(output, skoolfile)
        return skoolfile

    def _write_mm_skool(self):
        return self._write_skool(MMZ80, 'manic_miner', MM2CTL)

    def _write_rom_skool(self):
        return self._write_skool(ROM, 'rom', ctlfile=ROMCTL, org=0)

class AsmTestCase(DisassembliesTestCase):
    def _test_asm(self, options, skoolfile, clean=True):
        args = '{} {}'.format(options, skoolfile)
        output, stderr = self.run_skool2asm(args, err_lines=True)
        if clean:
            self.assertTrue(stderr[0].startswith('Parsed {}'.format(skoolfile)))
            self.assertEqual(len(stderr), 3)
        else:
            self.assertTrue(any([line.startswith('Parsed {}'.format(skoolfile)) for line in stderr]))
        self.assertTrue(stderr[-1].startswith('Wrote ASM to stdout'))

    def write_mm(self, options):
        self._test_asm(options, self._write_mm_skool(), False)

    def write_rom(self, options):
        self._test_asm(options, self._write_rom_skool(), False)

class CtlTestCase(DisassembliesTestCase):
    def _test_ctl(self, options, skoolfile):
        args = '{} {}'.format(options, skoolfile)
        output, stderr = self.run_skool2ctl(args)
        self.assertEqual(stderr, '')

    def write_mm(self, options):
        self._test_ctl(options, self._write_mm_skool())

    def write_rom(self, options):
        self._test_ctl(options, self._write_rom_skool())

class HtmlTestCase(DisassembliesTestCase):
    def setUp(self):
        DisassembliesTestCase.setUp(self)
        self.odir = 'html-{0}'.format(os.getpid())
        self.tempdirs.append(self.odir)

    def _validate_xhtml(self):
        if os.path.isfile(XHTML_XSD):
            xmlschema_doc = etree.parse(XHTML_XSD)
            xmlschema = etree.XMLSchema(xmlschema_doc)
            for root, dirs, files in os.walk(self.odir):
                for fname in files:
                    if fname[-5:] == '.html':
                        htmlfile = os.path.join(root, fname)
                        try:
                            xhtml = etree.parse(htmlfile)
                        except etree.LxmlError as e:
                            self.fail('Error while parsing {}: {}'.format(htmlfile, e.message))
                        try:
                            xmlschema.assertValid(xhtml)
                        except etree.DocumentInvalid as e:
                            self.fail('Error while validating {}: {}'.format(htmlfile, e.message))

    def _check_links(self):
        all_files, orphans, missing_files, missing_anchors = check_links(self.odir)
        if orphans or missing_files or missing_anchors:
            error_msg = []
            if orphans:
                error_msg.append('Orphaned files: {}'.format(len(orphans)))
                for fname in orphans:
                    error_msg.append('  {}'.format(fname))
            if missing_files:
                error_msg.append('Links to nonexistent files: {}'.format(len(missing_files)))
                for fname, link_dest in missing_files:
                    error_msg.append('  {} -> {}'.format(fname, link_dest))
            if missing_anchors:
                error_msg.append('Links to nonexistent anchors: {}'.format(len(missing_anchors)))
                for fname, link_dest in missing_anchors:
                    error_msg.append('  {} -> {}'.format(fname, link_dest))
            self.fail('\n'.join(error_msg))

    def _test_html(self, html_dir, options, ref_file, exp_output, skoolfile):
        cssfile = self.write_text_file(suffix='.css')
        c_options = '-c Game/StyleSheet={0}'.format(cssfile)
        c_options += ' -c Config/SkoolFile={0}'.format(skoolfile)
        shutil.rmtree(self.odir, True)

        # Write the disassembly
        output, error = self.run_skool2html('{} -d {} {} {}'.format(c_options, self.odir, options, ref_file))
        self.assertEqual(len(error), 0)
        reps = {'odir': self.odir, 'cssfile': cssfile, 'skoolfile': skoolfile, 'reffile': ref_file}
        self.assertEqual(output, exp_output.format(**reps).split('\n'))

        self._validate_xhtml()
        self._check_links()

    def write_mm(self, options):
        self._test_html('manic_miner', options, MMREF, OUTPUT_MM, self._write_mm_skool())

    def write_rom(self, options):
        self._test_html('rom', options, ROMREF, OUTPUT_ROM, self._write_rom_skool())

class SftTestCase(DisassembliesTestCase):
    def _test_sft(self, options, skoolfile, snapshot, org=None):
        with open(skoolfile, 'rt') as f:
            orig_skool = f.read().split('\n')
        args = '{} {}'.format(options, skoolfile)
        sft, stderr = self.run_skool2sft(args, out_lines=False)
        self.assertEqual(stderr, '')
        sftfile = self.write_text_file(sft)
        options = '-T {}'.format(sftfile)
        if org is not None:
            options += ' -o {}'.format(org)
        output, stderr = self.run_sna2skool('{} {}'.format(options, snapshot))
        self.assert_output_equal(output, orig_skool[:-1])

    def write_mm(self, options):
        self._test_sft(options, self._write_mm_skool(), MMZ80)

    def write_rom(self, options):
        self._test_sft(options, self._write_rom_skool(), ROM, 0)
