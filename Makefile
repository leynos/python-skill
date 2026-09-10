.DEFAULT_GOAL := check

# A pipeline reports only its last command's status by default, so a failing
# `git ls-files` would be masked by a successful `xargs`. pipefail propagates it.
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

MD_GLOB := **/*.md

# The skill manifest contract. SKILL_DIRS defaults to every shipped skill and
# can be overridden to check one skill or a test fixture, for example
# `make skill-manifest-check SKILL_DIRS=skills/ruff-016/`.
SKILL_DIRS ?= $(sort $(dir $(wildcard skills/*/SKILL.md)))
SKILLS_REF := uv run --group dev skills-ref
YAMLLINT := uv run --group dev yamllint
SKILL_YAMLLINT_CONFIG := {extends: default, rules: {line-length: disable}}

.PHONY: help fmt markdownlint nixie lint check check-fmt typecheck test \
	skill-frontmatter-lint skill-manifest-validate skill-manifest-check

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

fmt: ## Reflow Markdown tables and apply markdownlint fixes in place
	git ls-files -z '*.md' '*.markdown' \
	  | xargs -0 --no-run-if-empty \
	    mdtablefix --wrap --renumber --breaks --ellipsis --fences --in-place --
	markdownlint --fix '$(MD_GLOB)'

markdownlint: ## Lint every Markdown file
	markdownlint '$(MD_GLOB)'

nixie: ## Validate every Mermaid diagram
	nixie .

lint: markdownlint nixie skill-manifest-check ## Run all lint gates

# `set -e` matters: without it the loop exits with the status of its final
# iteration, so a conformant trailing skill would mask a malformed earlier one.
skill-frontmatter-lint: ## Lint each skill manifest's YAML frontmatter
	@set -euo pipefail; for skill_dir in $(SKILL_DIRS); do \
		skill_file="$${skill_dir%/}/SKILL.md"; \
		echo "yamllint $$skill_file frontmatter"; \
		awk 'NR == 1 { if ($$0 != "---") exit 1; print; next } $$0 == "---" { found = 1; print; exit } { print } END { if (!found) exit 1 }' "$$skill_file" \
		  | $(YAMLLINT) -d '$(SKILL_YAMLLINT_CONFIG)' -; \
	done

skill-manifest-validate: ## Validate each skill against the Agent Skills schema
	@set -eu; for skill_dir in $(SKILL_DIRS); do \
		echo "skills-ref validate $$skill_dir"; \
		$(SKILLS_REF) validate "$$skill_dir"; \
	done

skill-manifest-check: skill-frontmatter-lint skill-manifest-validate ## Verify every skill manifest

check-fmt: markdownlint ## Formatting gate

typecheck: ## Type-check the test suite
	uv run --group dev mypy

test: ## Run the test suite
	uv run --group dev pytest

check: lint check-fmt typecheck test ## Run every commit gate
