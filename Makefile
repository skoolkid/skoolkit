NOSETESTS27 ?= nosetests-2.7
NOSETESTS34 ?= python3.4 /usr/bin/nosetests
NOSETESTS35 ?= $(HOME)/Python/Python3.5/bin/nosetests
NOSETESTS36 ?= $(HOME)/Python/Python3.6/bin/nosetests
OPTIONS = -d build/html -t

OPTIONS += $(foreach theme,$(THEMES),-T $(theme))
OPTIONS += $(HTML_OPTS)

.PHONY: usage
usage:
	@echo "Targets:"
	@echo "  usage         show this help"
	@echo "  doc           build the documentation"
	@echo "  man           build the man pages"
	@echo "  clean         clean the documentation and man pages"
	@echo "  hh            build the Hungry Horace disassembly"
	@echo "  test[-all]    run core/all tests with current Python interpreter"
	@echo "  test27[-all]  run core/all tests with Python 2.7"
	@echo "  test3X[-all]  run core/all tests with Python 3.X (4<=X<=6)"
	@echo "  test-cover    run core tests with coverage info"
	@echo "  release       build a SkoolKit release tarball and zip archive"
	@echo "  tarball       build a SkoolKit release tarball"
	@echo "  deb           build a SkoolKit Debian package"
	@echo "  rpm           build a SkoolKit RPM package"
	@echo ""
	@echo "Variables:"
	@echo "  THEMES     CSS theme(s) to use"
	@echo "  HTML_OPTS  options passed to skool2html.py"

.PHONY: doc
doc:
	$(MAKE) -C sphinx html

.PHONY: man
man:
	$(MAKE) -C sphinx man

.PHONY: clean
clean:
	$(MAKE) -C sphinx clean

.PHONY: hh
hh:
	if [ ! -f build/hungry_horace.z80 ]; then ./tap2sna.py -d build @examples/hungry_horace.t2s; fi
	./sna2skool.py -c examples/hungry_horace.ctl build/hungry_horace.z80 > build/hungry_horace.skool
	./skool2html.py $(OPTIONS) -S build examples/hungry_horace.ref

.PHONY: write-disassembly-tests
write-disassembly-tests:
	for t in asm ctl html sft; do \
	    tools/write-hh-tests.py $$t > tests/test_hh_$$t.py; \
	done

.PHONY: remove-disassembly-tests
remove-disassembly-tests:
	rm -f tests/test_hh_*.py*

.PHONY: test
test: remove-disassembly-tests
	nosetests -w tests

.PHONY: test-all
test-all: write-disassembly-tests
	nosetests -w tests

.PHONY: test%
test%: remove-disassembly-tests
	$(NOSETESTS$*) -w tests

.PHONY: test%-all
test%-all: write-disassembly-tests
	$(NOSETESTS$*) -w tests

.PHONY: test-cover
test-cover: remove-disassembly-tests
	nosetests -w tests --with-coverage --cover-package=skoolkit --cover-erase

.PHONY: release
release:
	SKOOLKIT_HOME=`pwd` tools/mksktarball

.PHONY: tarball
tarball:
	SKOOLKIT_HOME=`pwd` tools/mksktarball -t

.PHONY: deb
deb:
	SKOOLKIT_HOME=`pwd` tools/mkskpkg deb

.PHONY: rpm
rpm:
	SKOOLKIT_HOME=`pwd` tools/mkskpkg rpm
