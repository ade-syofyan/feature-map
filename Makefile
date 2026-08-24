PYTHON ?= python3
CODEX_SKILL_DIR ?= $(HOME)/.codex/skills/feature-map
CLI := codex-skill/feature-map/scripts/feature_map_cli.py

.PHONY: test smoke install-codex

test:
	$(PYTHON) -m pytest tests -q

smoke:
	$(PYTHON) $(CLI) doctor
	tmp=$$(mktemp); out=$$(mktemp); \
	printf 'WORKFLOW PAYROLL Input: Attendance. Output: Payroll.\n' > "$$tmp"; \
	$(PYTHON) hooks/fm_blueprint.py "$$tmp" -o "$$out"; \
	grep -q 'payroll:' "$$out"; \
	rm -f "$$tmp" "$$out"

install-codex:
	mkdir -p "$(CODEX_SKILL_DIR)"
	rsync -a --delete codex-skill/feature-map/ "$(CODEX_SKILL_DIR)/"
	printf '%s\n' "$(CURDIR)" > "$(CODEX_SKILL_DIR)/plugin-root.txt"
	chmod +x "$(CODEX_SKILL_DIR)/scripts/feature_map_cli.py"
	@echo "Installed Codex skill to $(CODEX_SKILL_DIR)"
	@echo "Linked plugin root: $(CURDIR)"
