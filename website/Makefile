# Usage: make <target>
# e.g. make dev    → starts dev server
#      make build  → production build
#      make help   → list all targets

.PHONY: help install dev build preview lint typecheck clean prepare

# Config 

# Detect package manager (pnpm preferred)
PNPM := $(shell command -v pnpm 2>/dev/null)
NPM  := $(shell command -v npm 2>/dev/null)
PKG  := $(if $(PNPM),pnpm,npm)

# Default target 
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo ""
	@echo "  Purifyt Frontend – available targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) \
		| awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'
	@echo ""

# Setup 
install: ## Install all dependencies
	$(PKG) install

prepare: ## Generate Nuxt types (.nuxt/)
	$(PKG) run postinstall

# Development 
dev: ## Start development server (port 3001)
	$(PKG) run dev

# Build & Preview 
build: ## Build for production
	$(PKG) run build

preview: build ## Build then preview production bundle
	$(PKG) run preview

# Code Quality 
lint: ## Run ESLint
	$(PKG) run lint

lint-fix: ## Run ESLint and auto-fix
	$(PKG) run lint -- --fix

typecheck: ## Run TypeScript type checking
	$(PKG) run typecheck

# Maintenance 
clean: ## Remove build artifacts and cache
	@echo "Cleaning .output, .nuxt, node_modules..."
	@if exist .output      (rmdir /s /q .output)
	@if exist .nuxt        (rmdir /s /q .nuxt)
	@echo "Done."

clean-all: clean ## Remove everything including node_modules
	@if exist node_modules (rmdir /s /q node_modules)
	@echo "node_modules removed."

# Environment setup helpers 
env: ## Copy .env.example to .env (if not exists)
	@if not exist .env (copy .env.example .env && echo ".env created") else (echo ".env already exists")
