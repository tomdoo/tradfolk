SHELL := /bin/bash

-include .env
export

.PHONY: lint lint-backend lint-frontend lint-fix lint-fix-backend lint-fix-frontend format format-backend format-frontend check check-backend check-frontend check-fix check-fix-backend check-fix-frontend

NODE_IMAGE := node:20-alpine
PYTHON_IMAGE := python:3.12-slim
BACKEND_RUN := docker run --rm -v "$(CURDIR)/backend:/app" -w /app $(PYTHON_IMAGE) sh
BACKEND_LINT_CMD := pip install --no-cache-dir -q -r requirements-dev.txt && python -m ruff check app migrations
BACKEND_LINT_FIX_CMD := pip install --no-cache-dir -q -r requirements-dev.txt && python -m ruff format app migrations && python -m ruff check --fix app migrations
BACKEND_FORMAT_CMD := pip install --no-cache-dir -q -r requirements-dev.txt && python -m ruff format app migrations
BACKEND_CHECK_CMD := pip install --no-cache-dir -q -r requirements-dev.txt && python -m ruff check app migrations && python -m compileall app migrations
BACKEND_CHECK_FIX_CMD := pip install --no-cache-dir -q -r requirements-dev.txt && python -m ruff format app migrations && python -m ruff check --fix app migrations && python -m compileall app migrations
FRONTEND_LINT_CMD := npm install --silent && npm run lint
FRONTEND_LINT_FIX_CMD := npm install --silent && npm run lint:fix
FRONTEND_FORMAT_CMD := npm install --silent && npm run format
FRONTEND_CHECK_CMD := npm install --silent && npm run check
FRONTEND_CHECK_FIX_CMD := npm install --silent && npm run lint:fix && npm run format && npm run build

APP_ENV ?= prod
COMPOSE_FILES := -f docker-compose.yml

ifeq ($(APP_ENV),dev)
COMPOSE_FILES += -f docker-compose.dev.yml
endif

.PHONY: up down

up:
	docker compose $(COMPOSE_FILES) up --build

down:
	docker compose $(COMPOSE_FILES) down

lint: lint-backend lint-frontend

lint-backend:
	$(BACKEND_RUN) -lc "$(BACKEND_LINT_CMD)"

lint-frontend:
	docker run --rm -v "$(CURDIR)/frontend:/workspace" -w /workspace $(NODE_IMAGE) sh -lc "$(FRONTEND_LINT_CMD)"

lint-fix: lint-fix-backend lint-fix-frontend

lint-fix-backend:
	$(BACKEND_RUN) -lc "$(BACKEND_LINT_FIX_CMD)"

lint-fix-frontend:
	docker run --rm -v "$(CURDIR)/frontend:/workspace" -w /workspace $(NODE_IMAGE) sh -lc "$(FRONTEND_LINT_FIX_CMD)"

format: format-backend format-frontend

format-backend:
	$(BACKEND_RUN) -lc "$(BACKEND_FORMAT_CMD)"

format-frontend:
	docker run --rm -v "$(CURDIR)/frontend:/workspace" -w /workspace $(NODE_IMAGE) sh -lc "$(FRONTEND_FORMAT_CMD)"

check: check-backend check-frontend

check-backend:
	$(BACKEND_RUN) -lc "$(BACKEND_CHECK_CMD)"

check-frontend:
	docker run --rm -v "$(CURDIR)/frontend:/workspace" -w /workspace $(NODE_IMAGE) sh -lc "$(FRONTEND_CHECK_CMD)"

check-fix: check-fix-backend check-fix-frontend

check-fix-backend:
	$(BACKEND_RUN) -lc "$(BACKEND_CHECK_FIX_CMD)"

check-fix-frontend:
	docker run --rm -v "$(CURDIR)/frontend:/workspace" -w /workspace $(NODE_IMAGE) sh -lc "$(FRONTEND_CHECK_FIX_CMD)"
