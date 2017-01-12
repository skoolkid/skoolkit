ASM = $(shell grep ^GAME= .dreleaserc | cut -c6-).asm
ASM_OPTIONS = $(ASM_OPTS)
BUILD = build
HTML_OPTIONS = $(HTML_OPTS)
HTML_OPTIONS += -d $(BUILD)/html -t
HTML_OPTIONS += $(foreach theme,$(THEMES),-T $(theme))
NOSETESTS27 ?= nosetests-2.7
NOSETESTS34 ?= python3.4 /usr/bin/nosetests
NOSETESTS35 ?= $(HOME)/Python/Python3.5/bin/nosetests
NOSETESTS36 ?= $(HOME)/Python/Python3.6/bin/nosetests

.PHONY: usage
usage:
	@echo "Targets:"
	@echo "  usage     show this help"
	@echo "  html      build the HTML disassembly"
	@echo "  asm       build the ASM disassembly"
	@echo "  test      run tests with current Python interpreter"
	@echo "  test27    run tests with Python 2.7"
	@echo "  test3X    run tests with Python 3.X (4<=X<=6)"
	@$(MAKE) -s _targets
	@echo ""
	@echo "Variables:"
	@echo "  SKOOLKIT_HOME  directory containing the version of SkoolKit to use"
	@echo "  BUILD          directory in which to build the disassembly (default: build)"
	@echo "  THEMES         CSS theme(s) to use"
	@echo "  HTML_OPTS      extra options passed to skool2html.py"
	@echo "  ASM_OPTS       options passed to skool2asm.py"

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
	for t in asm ctl html sft; do utils/write-tests.py $$t > tests/test_$$t.py; done

.PHONY: test
test: write-tests
	nosetests -w tests

.PHONY: test%
test%: write-tests
	$(NOSETESTS$*) -w tests
