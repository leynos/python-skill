.DEFAULT_GOAL := check

# A pipeline reports only its last command's status by default, so a failing
# `git ls-files` would be masked by a successful `xargs`. pipefail propagates it.
SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

MD_GLOB := **/*.md

.PHONY: help fmt markdownlint nixie lint check check-fmt typecheck test

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

lint: markdownlint nixie ## Run all lint gates

check-fmt: markdownlint ## Formatting gate

typecheck: ## Type-check the test suite
	uv run --group dev mypy

test: ## Run the test suite
	uv run --group dev pytest

check: lint check-fmt typecheck test ## Run every commit gate
