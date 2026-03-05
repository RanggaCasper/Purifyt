.PHONY: venv install run dev test clean lint freeze docker-build docker-run

PYTHON = python
VENV = venv
PIP = $(VENV)/Scripts/pip
UVICORN = $(VENV)/Scripts/uvicorn
PYTEST = $(VENV)/Scripts/pytest
APP = app.main:app

# Create virtual environment
venv:
	@if not exist $(VENV) $(PYTHON) -m venv $(VENV)

# Install dependencies
install: venv
	$(PIP) install -r requirements.txt

# Run production server
run:
	$(UVICORN) $(APP) --host 0.0.0.0 --port 9000

# Run development server with hot reload
dev:
	$(UVICORN) $(APP) --reload --host 127.0.0.1 --port 9000

# Run tests
test:
	$(PYTEST) tests/ -v

# Clean up
clean:
	if exist $(VENV) rmdir /s /q $(VENV)
	if exist __pycache__ rmdir /s /q __pycache__
	for /d /r . %%d in (__pycache__) do @if exist "%%d" rmdir /s /q "%%d"
	for /r . %%f in (*.pyc) do @if exist "%%f" del "%%f"

# Freeze current dependencies
freeze:
	$(PIP) freeze > requirements.lock

# Docker build
docker-build:
	docker build -t purifyt .

# Docker run
docker-run:
	docker run -p 9000:9000 --env-file .env purifyt
