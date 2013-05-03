SKOOLKIT_HOME?=.
DARK?=0
SPECTRUM?=0
HEX?=0
SKOOL2HTML=$(SKOOLKIT_HOME)/skool2html.py
SNA2SKOOL=$(SKOOLKIT_HOME)/sna2skool.py
NOSETESTS26=/usr/bin/python2.6 /usr/bin/nosetests
NOSETESTS27=/usr/bin/python2.7 /usr/bin/nosetests
NOSETESTS31=$(HOME)/Python/Python3.1/bin/nosetests
NOSETESTS32=/usr/bin/python3.2 /usr/bin/nosetests
NOSETESTS33=$(HOME)/Python/Python3.3/bin/nosetests
OPTIONS=-d build/html -t

ifeq ($(DARK),1)
  OPTIONS+= -T dark
else ifeq ($(SPECTRUM),1)
  OPTIONS+= -T spectrum -c Paths/Font=spectrum.ttf
endif
ifeq ($(HEX),1)
  OPTIONS+= -H
endif

.PHONY: usage
usage:
	@echo "Supported targets:"
	@echo "  usage            show this help"
	@echo "  doc              build the documentation"
	@echo "  clean            clean the documentation"
	@echo "  mm               build the Manic Miner disassembly"
	@echo "  jsw              build the Jet Set Willy disassembly"
	@echo "  test[-all]       run core/all unit tests with current Python interpreter"
	@echo "  test2.6[-all]    run core/all unit tests with Python 2.6"
	@echo "  test2.7[-all]    run core/all unit tests with Python 2.7"
	@echo "  test3.1[-all]    run core/all unit tests with Python 3.1"
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
	@echo "  DARK=1           use the 'dark' theme when building a disassembly"
	@echo "  SPECTRUM=1       use the 'spectrum' theme when building a disassembly"
	@echo "  HEX=1            use hexadecimal when building a disassembly"

.PHONY: doc
doc:
	$(MAKE) -C sphinx html

.PHONY: clean
clean:
	$(MAKE) -C sphinx clean

.PHONY: mm
mm:
	$(SKOOLKIT_HOME)/utils/mm2ctl.py snapshots/manic_miner.z80 > manic_miner.ctl
	$(SNA2SKOOL) -c manic_miner.ctl snapshots/manic_miner.z80 > manic_miner.skool
	$(SKOOL2HTML) $(OPTIONS) examples/manic_miner.ref
	rm manic_miner.skool manic_miner.ctl

.PHONY: jsw
jsw:
	$(SKOOLKIT_HOME)/utils/jsw2ctl.py snapshots/jet_set_willy.z80 > jet_set_willy.ctl
	$(SNA2SKOOL) -c jet_set_willy.ctl snapshots/jet_set_willy.z80 > jet_set_willy.skool
	$(SKOOL2HTML) $(OPTIONS) examples/jet_set_willy.ref
	rm jet_set_willy.skool jet_set_willy.ctl

.PHONY: test
test:
	nosetests -w tests --ignore-files=test_disassemblies.py

.PHONY: test-all
test-all:
	nosetests -w tests

.PHONY: test2.6
test2.6:
	$(NOSETESTS26) -w tests --ignore-files=test_disassemblies.py

.PHONY: test2.6-all
test2.6-all:
	$(NOSETESTS26) -w tests

.PHONY: test2.7
test2.7:
	$(NOSETESTS27) -w tests --ignore-files=test_disassemblies.py

.PHONY: test2.7-all
test2.7-all:
	$(NOSETESTS27) -w tests

.PHONY: test3.1
test3.1:
	$(NOSETESTS31) -w tests --ignore-files=test_disassemblies.py

.PHONY: test3.1-all
test3.1-all:
	$(NOSETESTS31) -w tests

.PHONY: test3.2
test3.2:
	$(NOSETESTS32) -w tests --ignore-files=test_disassemblies.py

.PHONY: test3.2-all
test3.2-all:
	$(NOSETESTS32) -w tests

.PHONY: test3.3
test3.3:
	$(NOSETESTS33) -w tests --ignore-files=test_disassemblies.py

.PHONY: test3.3-all
test3.3-all:
	$(NOSETESTS33) -w tests

.PHONY: test-cover
test-cover:
	rm -rf tests/cover
	nosetests -w tests --with-coverage --cover-package=skoolkit --cover-html --cover-erase --ignore-files=test_disassemblies.py
	@echo "Coverage info in tests/cover/index.html"

.PHONY: test-cover-all
test-cover-all:
	rm -rf tests/cover
	nosetests -w tests --with-coverage --cover-package=skoolkit --cover-html --cover-erase
	@echo "Coverage info in tests/cover/index.html"

.PHONY: release
release:
	utils/mksktarball

.PHONY: tarball
tarball:
	utils/mksktarball -t

.PHONY: deb
deb:
	utils/mkskpkg deb

.PHONY: rpm
rpm:
	utils/mkskpkg rpm

DTD:
	curl -s http://www.w3.org/TR/xhtml1/xhtml1.tgz | tar xzf - xhtml1-20020801/DTD --strip-components=1

XSD:
	mkdir XSD
	curl -s http://www.w3.org/2002/08/xhtml/xhtml1-strict.xsd | sed 's@http://www.w3.org/2001/xml.xsd@xml.xsd@' > XSD/xhtml1-strict.xsd
	curl -s -o XSD/xml.xsd http://www.w3.org/2009/01/xml.xsd

.PHONY: snapshots
snapshots:
	utils/get-snapshots.py
