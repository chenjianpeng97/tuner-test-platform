# Code quality
.PHONY: code.format code.lint code.test code.cov code.cov.html code.check
code.format:
	ruff format

code.lint: code.format
	deptry
	slotscheck src
	lint-imports
	ruff check --exit-non-zero-on-fix
	mypy

code.test:
	pytest -v

code.cov:
	coverage run -m pytest
	coverage combine
	coverage report

code.cov.html:
	coverage run -m pytest
	coverage combine
	coverage html

code.check: code.lint code.test

# Environment
PYTHON := python
CONFIGS_DIG := config
TOML_CONFIG_MANAGER := $(CONFIGS_DIG)/toml_config_manager.py

.PHONY: guard-APP_ENV
guard-APP_ENV:
	@if [ -z "$$APP_ENV" ]; then \
		echo "APP_ENV is not set. Set APP_ENV before running this command."; \
		exit 1; \
	fi

.PHONY: env dotenv
env:
	@echo APP_ENV=$(APP_ENV)

dotenv: guard-APP_ENV
	@$(PYTHON) $(TOML_CONFIG_MANAGER) $(APP_ENV)

# Docker compose
DOCKER := docker
DOCKER_COMPOSE := docker compose
DOCKER_COMPOSE_PRUNE := scripts/makefile/docker_prune.sh

.PHONY: guard-docker
guard-docker:
	@command -v $(DOCKER) >/dev/null 2>&1 || { \
		echo "docker is required for this command but was not found in PATH."; \
		echo "Install Docker/Compose first, or run only the dependency setup target: pnpm exec nx run app-api:init"; \
		exit 1; \
	}

.PHONY: up.db up.db-echo up up.echo down down.total logs.db shell.db prune
up.db: guard-APP_ENV guard-docker
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up -d --wait web_app_db_pg

up.db-echo: guard-APP_ENV guard-docker
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up web_app_db_pg

up: guard-APP_ENV guard-docker
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up -d --build

up.echo: guard-APP_ENV guard-docker
	@echo "APP_ENV=$(APP_ENV)"
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) up --build

down.db: guard-APP_ENV guard-docker
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down web_app_db_pg

down: guard-APP_ENV guard-docker
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down

down.total: guard-APP_ENV guard-docker
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) down -v

logs.db: guard-APP_ENV guard-docker
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) logs -f web_app_db_pg

shell.db: guard-APP_ENV guard-docker
	@cd $(CONFIGS_DIG)/$(APP_ENV) && $(DOCKER_COMPOSE) --env-file .env.$(APP_ENV) exec web_app_db_pg sh

prune: guard-docker
	$(DOCKER_COMPOSE_PRUNE)

# Project structure visualization
PYCACHE_DEL := scripts/makefile/pycache_del.sh
DISHKA_PLOT_DATA := scripts/dishka/plot_dependencies_data.py

.PHONY: pycache-del tree plot-data
pycache-del:
	@$(PYCACHE_DEL)

# Clean tree
tree: pycache-del
	@tree

# Dishka
plot-data:
	@$(PYTHON) $(DISHKA_PLOT_DATA)
