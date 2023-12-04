.PHONY: install clean format lint tests build publish publish-test

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = cosimulation-toolkit
PACKAGE_NAME = cosimtlk
PACKAGE_VERSION := $(shell hatch version)
DOCKER_REPOSITORY = attilabalint/$(PACKAGE_NAME)
PYTHON_INTERPRETER = python3


#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Create python virtual environment
venv/bin/python:
	( \
		$(PYTHON_INTERPRETER) -m venv $(PROJECT_DIR)/venv; \
		source $(PROJECT_DIR)/venv/bin/activate; \
		pip install --upgrade pip; \
	)

## Initialize git repository
.git:
	@echo "Initializing git..."
	git init
	git add .
	git commit -m "Initial commit"

## Install project dependencies
install: venv/bin/python
	( \
		source $(PROJECT_DIR)/venv/bin/activate; \
		pip install -e .; \
    )

## Initialize project setup
setup: install .git

## Lint using ruff, mypy, black, and isort
lint:
	hatch run lint:all

## Format using black
format:
	hatch run lint:fmt

## Run pytest with coverage
tests:
	hatch run cov


#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Build source distribution and wheel
build: lint test
	hatch build

## Upload source distribution and wheel to PyPI
publish: build
	hatch publish --repo main

## Upload source distribution and wheel to TestPyPI
publish-test: build
	hatch publish --repo test

image:
	docker build --build-arg PYPI_VERSION=$(PACKAGE_VERSION) -t $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION) -f ./docker/Dockerfile .

dev-image:
	docker build --build-arg PYPI_VERSION=$(PACKAGE_VERSION) -t $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION) -f ./docker/dev/Dockerfile .

push-image: image
	docker push $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)

pull-image:
	docker pull $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)

run-image: image
	docker run -it -v ./fmus:/home/cosimtlk/fmus -p 8000:8000 --rm $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)

run-dev-image: dev-image
	docker run -it -v ./fmus:/home/cosimtlk/fmus -p 8000:8000 --rm $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)

#################################################################################
# Self Documenting Commands                                                     #
#################################################################################

.DEFAULT_GOAL := help

# Inspired by <http://marmelab.com/blog/2016/02/29/auto-documented-makefile.html>
# sed script explained:
# /^##/:
# 	* save line in hold space
# 	* purge line
# 	* Loop:
# 		* append newline + line to hold space
# 		* go to next line
# 		* if line starts with doc comment, strip comment character off and loop
# 	* remove target prerequisites
# 	* append hold space (+ newline) to line
# 	* replace newline plus comments by `---`
# 	* print line
# Separate expressions are necessary because labels cannot be delimited by
# semicolon; see <http://stackoverflow.com/a/11799865/1968>
.PHONY: help
help:
	@echo "$$(tput bold)Available rules:$$(tput sgr0)"
	@echo
	@sed -n -e "/^## / { \
		h; \
		s/.*//; \
		:doc" \
		-e "H; \
		n; \
		s/^## //; \
		t doc" \
		-e "s/:.*//; \
		G; \
		s/\\n## /---/; \
		s/\\n/ /g; \
		p; \
	}" ${MAKEFILE_LIST} \
	| LC_ALL='C' sort --ignore-case \
	| awk -F '---' \
		-v ncol=$$(tput cols) \
		-v indent=19 \
		-v col_on="$$(tput setaf 6)" \
		-v col_off="$$(tput sgr0)" \
	'{ \
		printf "%s%*s%s ", col_on, -indent, $$1, col_off; \
		n = split($$2, words, " "); \
		line_length = ncol - indent; \
		for (i = 1; i <= n; i++) { \
			line_length -= length(words[i]) + 1; \
			if (line_length <= 0) { \
				line_length = ncol - indent - length(words[i]) - 1; \
				printf "\n%*s ", -indent, " "; \
			} \
			printf "%s ", words[i]; \
		} \
		printf "\n"; \
	}' \
	| more $(shell test $(shell uname) = Darwin && echo '--no-init --raw-control-chars')
