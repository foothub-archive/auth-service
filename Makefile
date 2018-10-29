.PHONY: clean clean-test clean-pyc help
.DEFAULT_GOAL := help

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT


help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: clean-pyc clean-test ## remove all build, test, coverage and Python artifacts

clean-pyc: ## remove Python file artifacts
	find . | grep -E "(__pycache__|\.pyc$)" | xargs rm -rf

clean-test: ## remove test and coverage artifacts
	rm -f auth/.coverage \
	rm -fr auth/htmlcov/ \
	rm -fr .mypy_cache \

create-keys: ## creates a rsa key pair
	cd auth && j-crypto-create-pair && cd ..

create-keys-docker:
	docker-compose build
	docker-compose run --rm -p 8000:8000 web bash -c "python create_keys.py"
	docker-compose down

lint: # check style with flake8
	flake8 auth

type-check: ## check types with mypy
	mypy auth && rm -r .mypy_cache

test: # run django tests
	cd auth && python manage.py test -v 2 && cd ..

coverage: # run django tests with coverage
	cd auth && coverage run manage.py test -v 2 && coverage html && cd ..

tests:
	$(MAKE) lint
	$(MAKE) type-check
	$(MAKE) test

start-dev: # start development containers
	docker-compose build
	docker-compose run --rm -p 8000:8000 web bash -c "bash"
	docker-compose down
