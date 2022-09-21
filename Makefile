NOSE ?= nose2-3
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
	@echo "  test[-all]    run core/all tests with default Python 3 interpreter"
	@echo "  test3X[-all]  run core/all tests with Python 3.X (7<=X<=10)"
	@echo "  test-cover    run core tests with coverage info"
	@echo "  test-slow     run slow tests with default Python 3 interpreter"
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
	./skool2html.py $(OPTIONS) build/hungry_horace.skool examples/hungry_horace.ref

.PHONY: write-disassembly-tests
write-disassembly-tests:
	for t in asm ctl html; do \
	    tools/write-hh-tests.py $$t > tests/test_hh_$$t.py; \
	done

.PHONY: remove-disassembly-tests
remove-disassembly-tests:
	rm -f tests/test_hh_*.py*

.PHONY: test
test: remove-disassembly-tests
	$(NOSE)

.PHONY: test-all
test-all: write-disassembly-tests
	$(NOSE)

.PHONY: nose3%
nose3%:
	$(HOME)/Python/Python3.$*/bin/nose2

.PHONY: test%
test%: remove-disassembly-tests
	$(MAKE) nose$*

.PHONY: test%-all
test%-all: write-disassembly-tests
	$(MAKE) nose$*

.PHONY: test-cover
test-cover: remove-disassembly-tests
	$(NOSE) -C --coverage skoolkit --coverage-report term-missing

.PHONY: test-slow
test-slow:
	$(NOSE) -v -c tests/slow_test.cfg

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
