# Adapted from various Makefiles from projects under
# https://github.com/masschallenge.
# All aspects that are copyrighted by MassChallenge or Nathan Wilson
# are available under the MIT License.


help:
	@echo Valid targets are:
	@echo help - Prints this help message
	@echo code-check - Runs pycodestyle on all python code in the project
	@echo coverage - Use pytest to run all tests and report on test coverage
	@echo test - Use pytest to run all tests


VENV = venv
MODULE_NAME = mat

PROJECT_PYFILES = \
  mat/admin.py \
  mat/appdata.py \
  mat/ascii85.py \
  mat/calibration.py \
  mat/calibration_factories.py \
  mat/converter.py \
  mat/data_file_factory.py \
  mat/gps.py \
  mat/header.py \
  mat/lid_data_file.py \
  mat/lis_data_file.py \
  mat/matcomm.py \
  mat/sensor.py \
  mat/sensor_data_file.py \
  mat/sensor_specification.py \
  mat/setupfile.py \
  mat/tiltcurve.py \
  mat/utils.py \
  mat/v2_calibration.py \
  mat/v3_calibration.py \


ifeq ($(OS),Windows_NT)
  CP = copy
  GIT_HOOKS_TARGET = .git\hooks\pre-commit
  GIT_HOOKS_SOURCE = git-hooks\pre-commit
  PYTHON = python
  ACTIVATE = $(VENV)\Scripts\activate && set PYTHONPATH=.
  RMDIR_CMD := rmdir /s /q
  virtualenv = $(shell where virtualenv.exe)
else
  CP = cp
  GIT_HOOKS_TARGET = .git/hooks/pre-commit
  GIT_HOOKS_SOURCE = git-hooks/pre-commit
  PYTHON = python3
  VENV_PYTHON = -p $(PYTHON)
  ACTIVATE = export PYTHONPATH=.; . $(VENV)/bin/activate
  RMDIR_CMD = rm -rf
  virtualenv = $(shell which virtualenv)
endif


$(GIT_HOOKS_TARGET): $(GIT_HOOKS_SOURCE)
	@$(CP) $(GIT_HOOKS_SOURCE) $(GIT_HOOKS_TARGET)


ifeq ($(virtualenv),)
  NEED_VIRTUALENV = virtualenv
endif

virtualenv:
	@pip install virtualenv


$(VENV): $(NEED_VIRTUALENV) requirements.txt $(GIT_HOOKS_TARGET)
	@-$(RMDIR_CMD) $(VENV)
	@virtualenv $(VENV_PYTHON) $@
	@$(ACTIVATE) && pip install -r requirements.txt


code-check: $(VENV)
	@$(ACTIVATE) && flake8 $(PROJECT_PYFILES)


test: $(VENV)
	@$(ACTIVATE) && pytest


coverage: $(VENV)
	@$(ACTIVATE) && pytest --cov=$(MODULE_NAME) \
		--cov-report=term --cov-report=html
