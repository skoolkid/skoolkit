DARK?=0
SPECTRUM?=0
HEX?=0
ROM?=/usr/share/spectrum-roms/48.rom
NOSETESTS27=/usr/bin/python2.7 /usr/bin/nosetests
NOSETESTS32=/usr/bin/python3.2 /usr/bin/nosetests
NOSETESTS33=$(HOME)/Python/Python3.3/bin/nosetests
OPTIONS=-d build/html -t

OPTIONS+=$(foreach theme,$(THEMES),-T $(theme))
ifeq ($(findstring spectrum,$(THEMES)),spectrum)
  OPTIONS+=-c Game/Font=spectrum.ttf
endif
ifeq ($(HEX),1)
  OPTIONS+=-H
endif

.PHONY: usage
usage:
	@echo "Supported targets:"
	@echo "  usage            show this help"
	@echo "  doc              build the documentation"
	@echo "  man              build the man pages"
	@echo "  clean            clean the documentation and man pages"
	@echo "  mm               build the Manic Miner disassembly"
	@echo "  jsw              build the Jet Set Willy disassembly"
	@echo "  rom              build the Spectrum ROM disassembly"
	@echo "  test[-all]       run core/all unit tests with current Python interpreter"
	@echo "  test2.7[-all]    run core/all unit tests with Python 2.7"
	@echo "  test3.2[-all]    run core/all unit tests with Python 3.2"
	@echo "  test3.3[-all]    run core/all unit tests with Python 3.3"
	@echo "  test-cover[-all] run core/all unit tests with coverage info"
	@echo "  release          build a SkoolKit release tarball and zip archive"
	@echo "  tarball          build a SkoolKit release tarball"
	@echo "  deb              build a SkoolKit Debian package"
	@echo "  rpm              build a SkoolKit RPM package"
	@echo "  DTD              download XHTML DTDs"
	@echo "  XSD              download XHTML XSDs"
	@echo "  snapshots        build snapshots of Manic Miner and Jet Set Willy"
	@echo ""
	@echo "Environment variables:"
	@echo "  THEMES           CSS theme(s) to use"
	@echo "  HEX=1            use hexadecimal when building a disassembly"
	@echo "  ROM              path to the Spectrum ROM dump"

.PHONY: doc
doc:
	$(MAKE) -C sphinx html

.PHONY: man
man:
	$(MAKE) -C man man

.PHONY: clean
clean:
	$(MAKE) -C sphinx clean
	$(MAKE) -C man clean

.PHONY: mm
mm:
	SKOOLKIT_HOME=`pwd` utils/mm2ctl.py snapshots/manic_miner.z80 > manic_miner.ctl
	./sna2skool.py -c manic_miner.ctl snapshots/manic_miner.z80 > manic_miner.skool
	./skool2html.py $(OPTIONS) examples/manic_miner.ref
	rm manic_miner.skool manic_miner.ctl

.PHONY: jsw
jsw:
	SKOOLKIT_HOME=`pwd` utils/jsw2ctl.py snapshots/jet_set_willy.z80 > jet_set_willy.ctl
	./sna2skool.py -c jet_set_willy.ctl snapshots/jet_set_willy.z80 > jet_set_willy.skool
	./skool2html.py $(OPTIONS) examples/jet_set_willy.ref
	rm jet_set_willy.skool jet_set_willy.ctl

.PHONY: rom
rom:
	./sna2skool.py -o 0 -H -c examples/48.rom.ctl $(ROM) > 48.rom.skool
	./skool2html.py $(OPTIONS) examples/48.rom.ref
	rm 48.rom.skool

.PHONY: write-disassembly-tests
write-disassembly-tests:
	for t in asm ctl html sft; do utils/write-disassembly-tests.py $$t > tests/test_disassemblies_$$t.py; done

.PHONY: remove-disassembly-tests
remove-disassembly-tests:
	rm -f tests/test_disassemblies_*.py*

.PHONY: test
test: remove-disassembly-tests
	nosetests -w tests

.PHONY: test-all
test-all: write-disassembly-tests
	nosetests -w tests

.PHONY: test2.7
test2.7: remove-disassembly-tests
	$(NOSETESTS27) -w tests

.PHONY: test2.7-all
test2.7-all: write-disassembly-tests
	$(NOSETESTS27) -w tests

.PHONY: test3.2
test3.2: remove-disassembly-tests
	$(NOSETESTS32) -w tests

.PHONY: test3.2-all
test3.2-all: write-disassembly-tests
	$(NOSETESTS32) -w tests

.PHONY: test3.3
test3.3: remove-disassembly-tests
	$(NOSETESTS33) -w tests

.PHONY: test3.3-all
test3.3-all: write-disassembly-tests
	$(NOSETESTS33) -w tests

.PHONY: test-cover
test-cover: remove-disassembly-tests
	rm -rf tests/cover
	nosetests -w tests --with-coverage --cover-package=skoolkit --cover-html --cover-erase
	@echo "Coverage info in tests/cover/index.html"

.PHONY: test-cover-all
test-cover-all: write-disassembly-tests
	rm -rf tests/cover
	nosetests -w tests --with-coverage --cover-package=skoolkit --cover-html --cover-erase
	@echo "Coverage info in tests/cover/index.html"

.PHONY: release
release:
	SKOOLKIT_HOME=`pwd` utils/mksktarball

.PHONY: tarball
tarball:
	SKOOLKIT_HOME=`pwd` utils/mksktarball -t

.PHONY: deb
deb:
	SKOOLKIT_HOME=`pwd` utils/mkskpkg deb

.PHONY: rpm
rpm:
	SKOOLKIT_HOME=`pwd` utils/mkskpkg rpm

DTD:
	curl -s http://www.w3.org/TR/xhtml1/xhtml1.tgz | tar xzf - --strip-components=1 xhtml1-20020801/DTD

XSD:
	mkdir XSD
	curl -s http://www.w3.org/2002/08/xhtml/xhtml1-strict.xsd | sed 's@http://www.w3.org/2001/xml.xsd@xml.xsd@' > XSD/xhtml1-strict.xsd
	curl -s -o XSD/xml.xsd http://www.w3.org/2009/01/xml.xsd

.PHONY: snapshots
snapshots:
	./tap2sna.py -d snapshots @examples/manic_miner.t2s
	./tap2sna.py -d snapshots @examples/jet_set_willy.t2s
