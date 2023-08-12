.PHONY: install clean format lint tests build publish publish-test

#################################################################################
# GLOBALS                                                                       #
#################################################################################

PROJECT_DIR := $(shell dirname $(realpath $(lastword $(MAKEFILE_LIST))))
PROJECT_NAME = cosimulation-toolkit
PACKAGE_NAME = cosimtlk
PACKAGE_VERSION := $(shell hatch version)
DOCKER_REPOSITORY = attilabalint/$(PACKAGE_NAME)


#################################################################################
# COMMANDS                                                                      #
#################################################################################

## Install project dependencies
install:
	pip install -U pip
	pip install -e ."[test,dev]"
	mypy --install-types

## Delete all compiled Python files
clean:
	find . -type f -name "*.py[co]" -delete
	find . -type d -name "__pycache__" -delete

## Format using black
format:
	ruff src tests --fix
	black src tests
	isort src tests

## Lint using ruff, mypy, black, and isort
lint: format
	mypy src
	ruff src tests
	black src tests --check
	isort src tests --check-only

## Run pytest with coverage
tests:
	pytest src tests

#################################################################################
# PROJECT RULES                                                                 #
#################################################################################

## Build source distribution and wheel
build: lint tests
	hatch build

## Upload source distribution and wheel to PyPI
publish: build
	hatch publish --repo main

## Upload source distribution and wheel to TestPyPI
publish-test: build
	hatch publish --repo test

image:
	docker build --build-arg PYPI_VERSION=$(PACKAGE_VERSION) -t $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION) .

push-image:
	docker push $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)

pull-image:
	docker pull $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)

container:
	docker run -it -v ./examples/fmus:/home/cosimtlk/fmus -p 3000:8000 --rm $(DOCKER_REPOSITORY):v$(PACKAGE_VERSION)


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
