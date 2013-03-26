SKOOLKIT_HOME?=.
SKOOL2HTML=$(SKOOLKIT_HOME)/skool2html.py
SNA2SKOOL=$(SKOOLKIT_HOME)/sna2skool.py
NOSETESTS26=/usr/bin/python2.6 /usr/bin/nosetests
NOSETESTS27=/usr/bin/python2.7 /usr/bin/nosetests
NOSETESTS31=$(HOME)/Python/Python3.1/bin/nosetests
NOSETESTS32=/usr/bin/python3.2 /usr/bin/nosetests
NOSETESTS33=$(HOME)/Python/Python3.3/bin/nosetests
OPTIONS=-d build/html -t

ifdef DARK
  OPTIONS+= -c Paths/StyleSheet=skoolkit-dark.css
endif
ifdef SPECTRUM
  OPTIONS+= -c Paths/StyleSheet=skoolkit-spectrum.css -c Paths/Font=spectrum.ttf
endif
ifdef HEX
  OPTIONS+= -H
endif

.PHONY: usage
usage:
	@echo "Supported targets:"
	@echo "  usage        show this help"
	@echo "  doc          build the documentation"
	@echo "  clean        clean the documentation"
	@echo "  mm           build the Manic Miner disassembly"
	@echo "  jsw          build the Jet Set Willy disassembly"
	@echo "  test         run unit tests with current Python interpreter"
	@echo "  test2.6      run unit tests with Python 2.6"
	@echo "  test2.7      run unit tests with Python 2.7"
	@echo "  test3.1      run unit tests with Python 3.1"
	@echo "  test3.2      run unit tests with Python 3.2"
	@echo "  test3.3      run unit tests with Python 3.3"
	@echo "  test-cover   run unit tests with coverage info"
	@echo "  release      build a SkoolKit release tarball and zip archive"
	@echo "  tarball      build a SkoolKit release tarball"
	@echo "  deb          build a SkoolKit Debian package"
	@echo "  deb-clean    clean up after 'make deb'"
	@echo ""
	@echo "Environment variables:"
	@echo "  DARK=1       use skoolkit-dark.css when building a disassembly"
	@echo "  SPECTRUM=1   use skoolkit-spectrum.css when building a disassembly"
	@echo "  HEX=1        use hexadecimal when building a disassembly"

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
	nosetests -w tests

.PHONY: test2.6
test2.6:
	$(NOSETESTS26) -w tests

.PHONY: test2.7
test2.7:
	$(NOSETESTS27) -w tests

.PHONY: test3.1
test3.1:
	$(NOSETESTS31) -w tests

.PHONY: test3.2
test3.2:
	$(NOSETESTS32) -w tests

.PHONY: test3.3
test3.3:
	$(NOSETESTS33) -w tests

.PHONY: test-cover
test-cover:
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
deb: clean doc
	rsync -a --exclude=.buildinfo --exclude=objects.inv sphinx/build/html/ docs
	utils/mm2ctl.py snapshots/manic_miner.z80 > examples/manic_miner.ctl
	utils/jsw2ctl.py snapshots/jet_set_willy.z80 > examples/jet_set_willy.ctl
	rm -rf man/man1
	mkdir man/man1
	for m in bin2tap.py.rst skool2asm.py.rst skool2ctl.py.rst skool2html.py.rst skool2sft.py.rst sna2skool.py.rst; do rst2man man/$$m man/man1/$$(basename $$m .rst).1; done
	debuild -b -us -uc
	mkdir -p dist
	mv ../skoolkit_*.deb dist

.PHONY: deb-clean
deb-clean:
	rm -rf ../skoolkit_*.build ../skoolkit_*.changes build docs debian/skoolkit debian/files debian/skoolkit.debhelper.log debian/skoolkit.postinst.debhelper debian/skoolkit.prerm.debhelper debian/skoolkit.substvars examples/manic_miner.ctl examples/jet_set_willy.ctl man/man1
