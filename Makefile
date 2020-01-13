# Common User Targets:
#
#	make tests
#		- Sxecute the tests
#
#	make shell
#		- Set up the environment and drop to a shell (re-uses existing shells if they
#		  have already been set up).
#		  Use ctrl-d or `exit` to leave the shell.
#
#	PYTHON_TOOL=python2 make <target>
#		- Build the target requested, using python 2
#
#
# Assumptions:
#	* Python 3 is installed as `python3`. Use the PYTHON_TOOL variable to test using a
#	  specific python binary.
#	* The 'virtualenv' tool is installed.
#


PYTHON_TOOL ?= python3
ACTIVATE = source venv/${PYTHON_TOOL}/bin/activate

.PHONY: tests venv

TEST_MODULES = ${patsubst tests/%.py,%,$(wildcard tests/test_*.py)}

ifeq (${NOCOLOUR},)
COL_NOTICE = "\\e[35m"
COL_GOOD = "\\e[32m"
COL_RESET = "\\e[0m"
else
COL_NOTICE = ""
COL_GOOD = ""
COL_RESET = ""
endif

NOTICE = @notice() { printf "\n${COL_NOTICE}+++ %s${COL_RESET}\n" "$$@"; } && notice
GOOD = @notice() { printf "\n${COL_GOOD}+++ %s${COL_RESET}\n" "$$@"; } && notice


tests: test_testable
	${NOTICE} "Running tests"
	@# Note: We cd into the tests directory, so that we are testing the installed version, not
	@# 		the version in the repository.
	${ACTIVATE} && cd tests && python -munittest -v ${TEST_MODULES}
	${GOOD} "Tests passed"

venv: venv/successful-${PYTHON_TOOL}

venv/successful-${PYTHON_TOOL}:
	${NOTICE} "Build the virtualenv we will test within (for ${PYTHON_TOOL})"
	-rm -rf venv
	mkdir -p venv
	virtualenv -p ${PYTHON_TOOL} venv/${PYTHON_TOOL}
	touch venv/successful-${PYTHON_TOOL}

test_installable: venv
	${NOTICE} "Check that we can install the product"
	${ACTIVATE} && python setup.py install

test_testable: test_installable
	${NOTICE} "Install the test requirements"
	${ACTIVATE} && pip install -r requirements-test.txt

clean:
	${NOTICE} "Cleaning temporary files"
	-rm -rf venv dist build
	-find . -name '*.pyc' -delete
	-find . -name '__pycache__' -delete
	${GOOD} "Cleaned"

shell: venv
	${NOTICE} "Running shell; use ctrl-d or `exit` to leave"
	bash -i <<<"${ACTIVATE} && exec < /dev/tty"
	${GOOD} "Returned to user shell"
