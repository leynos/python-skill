.DEFAULT_GOAL := check

MD_GLOB := **/*.md
MD_FILES = $(shell git ls-files '*.md' '*.markdown')

.PHONY: help fmt markdownlint nixie lint check check-fmt typecheck test

help: ## Show this help
	@grep -hE '^[a-zA-Z_-]+:.*## ' $(MAKEFILE_LIST) \
	  | awk 'BEGIN {FS = ":.*## "}; {printf "  %-14s %s\n", $$1, $$2}'

fmt: ## Reflow Markdown tables and apply markdownlint fixes in place
	mdtablefix --wrap --renumber --breaks --ellipsis --fences --in-place \
	  $(MD_FILES)
	markdownlint --fix '$(MD_GLOB)'

markdownlint: ## Lint every Markdown file
	markdownlint '$(MD_GLOB)'

nixie: ## Validate every Mermaid diagram
	nixie .

lint: markdownlint nixie ## Run all lint gates

check-fmt: markdownlint ## Formatting gate (Markdown-only repository)

typecheck: ## No-op: this repository carries no typed source
	@echo "typecheck: no source to check (Markdown-only repository)"

test: ## No-op: this repository carries no executable source
	@echo "test: no test suite (Markdown-only repository)"

check: lint check-fmt typecheck test ## Run every commit gate
