ASM = $(shell grep ^GAME= .dreleaserc | cut -c6-).asm
ASM_OPTIONS = $(ASM_OPTS)
BUILD = build
HTML_OPTIONS = $(HTML_OPTS)
HTML_OPTIONS += -d $(BUILD)/html -t
HTML_OPTIONS += $(foreach theme,$(THEMES),-T $(theme))
TESTS ?= asm ctl html
CORES ?= 0

.PHONY: usage
usage:
	@echo "Targets:"
	@echo "  usage     show this help"
	@echo "  html      build the HTML disassembly"
	@echo "  asm       build the ASM disassembly"
	@echo "  test      run tests"
	@echo "  test3X    run tests with Python 3.X (8<=X<=12)"
	@$(MAKE) -s _targets
	@echo ""
	@echo "Variables:"
	@echo "  SKOOLKIT_HOME  directory containing the version of SkoolKit to use"
	@echo "  BUILD          directory in which to build the disassembly (default: build)"
	@echo "  THEMES         CSS theme(s) to use"
	@echo "  HTML_OPTS      extra options passed to skool2html.py"
	@echo "  ASM_OPTS       options passed to skool2asm.py"
	@echo "  CORES          number of processes to use when running tests"

.PHONY: _targets
_targets:

.PHONY: html
html:
	utils/mkhtml.py $(HTML_OPTIONS)

.PHONY: asm
asm:
	mkdir -p $(BUILD)/asm
	utils/mkasm.py $(ASM_OPTIONS) > $(BUILD)/asm/$(ASM)

.PHONY: write-tests
write-tests:
	mkdir -p tests
	rm -f tests/test_*.py
	for t in $(TESTS); do utils/write-tests.py $$t > tests/test_$$t.py; done

.PHONY: test
test: write-tests
	nose2-3 --plugin=nose2.plugins.mp -N $(CORES)

.PHONY: test3%
test3%: write-tests
	$(HOME)/Python/Python3.$*/bin/nose2 --plugin=nose2.plugins.mp -N $(CORES)
