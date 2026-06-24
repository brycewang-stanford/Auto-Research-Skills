PYTHON ?= python3
SAFETY_ROOTS ?= skills
SAFETY_MAX_FINDINGS ?= 50
SAFETY_CONTEXT ?=
SITE_HOST ?= 127.0.0.1
SITE_PORT ?= 8765

.PHONY: check repo-check docs-check catalog catalog-check index index-check site-check site-js-check serve-site count-skills safety-scan safety-report safety-report-check quality-report quality-report-check health-report py-compile shell-check test

check: py-compile shell-check test repo-check docs-check catalog-check index-check site-check site-js-check safety-report-check quality-report-check count-skills

repo-check:
	$(PYTHON) scripts/check-repo.py

docs-check:
	$(PYTHON) tools/check_docs.py

catalog:
	$(PYTHON) tools/build_catalog.py
	$(PYTHON) tools/build_index.py

catalog-check:
	$(PYTHON) tools/build_catalog.py --check

index:
	$(PYTHON) tools/build_index.py

index-check:
	$(PYTHON) tools/build_index.py --check

site-check:
	$(PYTHON) tools/check_site.py

site-js-check:
	@if command -v node >/dev/null 2>&1; then \
		for file in site/*.js; do node --check "$$file"; done; \
	else \
		echo "node not installed; skipped site/*.js syntax check"; \
	fi

serve-site:
	@echo "Serving http://$(SITE_HOST):$(SITE_PORT)/site/"
	$(PYTHON) -m http.server $(SITE_PORT) --bind $(SITE_HOST)

count-skills:
	./scripts/count-skills.sh

safety-scan:
	$(PYTHON) scripts/scan-skill-safety.py $(SAFETY_ROOTS) --max-findings $(SAFETY_MAX_FINDINGS) --fail-on none $(if $(SAFETY_CONTEXT),--context $(SAFETY_CONTEXT))

safety-report:
	$(PYTHON) tools/build_safety_report.py

safety-report-check:
	$(PYTHON) tools/build_safety_report.py --check

quality-report:
	$(PYTHON) tools/build_quality_report.py

quality-report-check:
	$(PYTHON) tools/build_quality_report.py --check

health-report:
	$(PYTHON) scripts/check-submodule-health.py

py-compile:
	$(PYTHON) -m py_compile scripts/check-repo.py tools/build_catalog.py tools/build_index.py tools/build_safety_report.py tools/build_quality_report.py tools/check_docs.py tools/check_site.py scripts/scan-skill-safety.py scripts/update-stars.py scripts/check-submodule-health.py scripts/discover-skills.py

shell-check:
	@for file in setup.sh scripts/count-skills.sh; do \
		bash -n "$$file"; \
	done

test:
	$(PYTHON) -m unittest discover -s tests
	@if $(PYTHON) -c "import pytest" >/dev/null 2>&1; then \
		$(PYTHON) -m pytest; \
	else \
		echo "pytest not installed; skipped pytest-style tests"; \
	fi
