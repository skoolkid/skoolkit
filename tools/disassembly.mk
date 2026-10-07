ASM = $(shell grep ^GAME= .dreleaserc | cut -c6-).asm
ASM_OPTIONS = $(ASM_OPTS)
BUILD = build
HTML_OPTIONS = $(HTML_OPTS)
HTML_OPTIONS += -d $(BUILD)/html -t
HTML_OPTIONS += $(foreach theme,$(THEMES),-T $(theme))
TESTS ?= asm ctl html
LSCPU = $(shell command -v lscpu)
CORES ?= $(if $(LSCPU),$(shell $(LSCPU) -p=SOCKET,CORE | grep -v '^#' | sort -u | wc -l),0)
SNAPSHOT_CMD ?= $(SKOOLKIT_HOME)/tap2sna.py @$(T2S) $(SNAPSHOT)

.PHONY: usage
usage:
	@echo "Targets:"
	@echo "  usage     show this help"
	@echo "  html      build the HTML disassembly"
	@echo "  asm       build the ASM disassembly"
	@echo "  test      run tests"
	@echo "  test3X    run tests with Python 3.X (10<=X<=14)"
	@echo "  snapshot  create $(SNAPSHOT)"
	@echo ""
	@echo "Variables:"
	@echo "  SKOOLKIT_HOME  directory containing the version of SkoolKit to use"
	@echo "  BUILD          directory in which to build the disassembly (default: build)"
	@echo "  THEMES         CSS theme(s) to use"
	@echo "  HTML_OPTS      extra options passed to skool2html.py"
	@echo "  ASM_OPTS       options passed to skool2asm.py"
	@echo "  CORES          number of processes to use when running tests"

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

.PHONY: snapshot
snapshot:
	if [ ! -f $(SNAPSHOT) ]; then $(SNAPSHOT_CMD); fi
