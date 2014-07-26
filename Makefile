
clean_pyc:
	find bttrtwisted bttrtwisted_tests -name "*.pyc" | xargs rm -f

pyflakes:
	pyflakes bttrtwisted bttrtwisted_tests

pylint:
	pylint --rcfile=conf/pylintrc bttrtwisted bttrtwisted_tests


.PHONY: lint
lint: clean_pyc pyflakes pylint

test:
	trial bttrtwisted_tests

tests: lint
tests: test
