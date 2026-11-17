.PHONY: install lint test dev ingest eval eval-live docker

PYTHON ?= python3
VENV ?= .venv
ifneq ($(wildcard $(VENV)/bin/python),)
  PY := $(VENV)/bin/python
  RUFF := $(VENV)/bin/ruff
  PYTEST := $(VENV)/bin/pytest
else
  PY := $(PYTHON)
  RUFF := $(PYTHON) -m ruff
  PYTEST := $(PYTHON) -m pytest
endif

install:
	@if $(PYTHON) -m venv $(VENV) 2>/dev/null && test -x $(VENV)/bin/pip; then \
	  $(VENV)/bin/pip install -U pip && $(VENV)/bin/pip install -r requirements.txt; \
	  echo "OK: $(VENV)"; \
	else \
	  rm -rf $(VENV); \
	  echo "venv failed — installing with $(PYTHON) -m pip"; \
	  $(PYTHON) -m pip install -r requirements.txt; \
	fi

lint:
	$(RUFF) check src tests

test:
	RAG_OFFLINE=1 $(PYTEST) -q

dev:
	@echo "Starting uvicorn src.main:app on :8765"
	@test -f src/main.py || (echo "src/main.py missing"; exit 1)
	$(PY) -m uvicorn src.main:app --host 0.0.0.0 --port 8765 --reload

ingest:
	$(PY) -m src.ingest --rebuild

eval:
	RAG_OFFLINE=1 $(PY) scripts/run_eval.py --offline

eval-live:
	$(PY) scripts/run_eval.py --live

docker:
	@test -f Dockerfile || (echo "Dockerfile missing"; exit 1)
	docker compose up --build