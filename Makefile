NOSE ?= nose2-3
CORES ?= 0
OPTIONS = -d build/html -t

OPTIONS += $(foreach theme,$(THEMES),-T $(theme))
OPTIONS += $(HTML_OPTS)

.PHONY: usage
usage:
	@echo "Targets:"
	@echo "  usage           show this help"
	@echo "  doc             build the documentation"
	@echo "  man             build the man pages"
	@echo "  clean           clean the documentation and man pages"
	@echo "  cmods           build and install the C extension modules"
	@echo "  hh              build the Hungry Horace disassembly"
	@echo "  test[-c]        run core tests [with C extension modules]"
	@echo "  test[-c]-3X     run core tests with Python 3.X (8<=X<=12) [and C extension modules]"
	@echo "  test[-c]-slow   run slow tests [with C extension modules]"
	@echo "  test[-c]-cmio   run timing tests for [C]CMIOSimulator"
	@echo "  test[-c]-all    run core and disassembly tests [with C extension modules]"
	@echo "  test[-c]-3X-all run core and disassembly tests with Python 3.X (8<=X<=12) [and C extension modules]"
	@echo "  test-cover      run core tests with coverage info"
	@echo "  release         build a SkoolKit release tarball and zip archive"
	@echo "  tarball         build a SkoolKit release tarball"
	@echo "  deb             build a SkoolKit Debian package"
	@echo "  rpm             build a SkoolKit RPM package"
	@echo ""
	@echo "Variables:"
	@echo "  THEMES     CSS theme(s) to use"
	@echo "  HTML_OPTS  options passed to skool2html.py"
	@echo "  CORES      number of processes to use when running tests"

.PHONY: doc
doc:
	$(MAKE) -C sphinx html

.PHONY: man
man:
	$(MAKE) -C sphinx man

.PHONY: clean
clean:
	$(MAKE) -C sphinx clean

.PHONY: cmods
cmods:
	python3 setup.py build_ext -i

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
	rm -f tests/test_hh_*.py

.PHONY: remove-c
remove-c:
	rm -f skoolkit/*.so

.PHONY: test
test: remove-disassembly-tests remove-c
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-c
test-c: remove-disassembly-tests cmods
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-all
test-all: write-disassembly-tests remove-c
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-c-all
test-c-all: write-disassembly-tests cmods
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-3%
test-3%: remove-disassembly-tests remove-c
	$(HOME)/Python/Python3.$*/bin/nose2 --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-c-3%
test-c-3%: remove-disassembly-tests
	$(HOME)/Python/Python3.$*/bin/python3 setup.py build_ext -b .
	$(HOME)/Python/Python3.$*/bin/nose2 --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-3%-all
test-3%-all: write-disassembly-tests remove-c
	$(HOME)/Python/Python3.$*/bin/nose2 --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-c-3%-all
test-c-3%-all: write-disassembly-tests
	$(HOME)/Python/Python3.$*/bin/python3 setup.py build_ext -b .
	$(HOME)/Python/Python3.$*/bin/nose2 --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test-slow
test-slow: remove-c
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES) -c tests/slow_test.cfg

.PHONY: test-c-slow
test-c-slow: cmods
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES) -c tests/slow_test.cfg

.PHONY: test-cmio
test-cmio:
	tools/write-cmiosimulator-tests.py --quiet --vslow
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES) slow_test_cmiosimulator
	rm slow_test_cmiosimulator.py

.PHONY: test-c-cmio
test-c-cmio: cmods
	tools/write-cmiosimulator-tests.py --quiet --vslow --ccmio
	$(NOSE) --plugin=nose2.plugins.mp -N $(CORES) slow_test_ccmiosimulator
	rm slow_test_ccmiosimulator.py

.PHONY: test-cover
test-cover: remove-disassembly-tests remove-c
	$(NOSE) -C --coverage skoolkit --coverage-report term-missing

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
