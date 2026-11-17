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
	  echo "venv ei õnnestunud — installin user/site pipiga ($(PYTHON) -m pip)"; \
	  $(PYTHON) -m pip install -r requirements.txt; \
	fi

lint:
	$(RUFF) check src tests

test:
	RAG_OFFLINE=1 $(PYTEST) -q

dev:
	@echo "FastAPI (samm 2): uvicorn src.main:app --host 0.0.0.0 --port 8765 --reload"
	@test -f src/main.py || (echo "src/main.py puudub — tee kõigepealt samm 1–2"; exit 1)
	$(PY) -m uvicorn src.main:app --host 0.0.0.0 --port 8765 --reload

ingest:
	@echo "RAG ingest (samm 1): python -m src.ingest"
	$(PY) -m src.ingest --help 2>/dev/null || (echo "src/ingest.py puudub — samm 1"; exit 1)

eval:
	RAG_OFFLINE=1 $(PY) scripts/run_eval.py --offline 2>/dev/null || echo "eval — samm 6"

eval-live:
	$(PY) scripts/run_eval.py --live 2>/dev/null || echo "eval-live — samm 6"

docker:
	@test -f Dockerfile || (echo "Dockerfile puudub — samm 3"; exit 1)
	docker compose up --build