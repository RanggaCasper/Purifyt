.PHONY: venv activate install run dev test clean freeze build-python build-desktop docker-build docker-run

PYTHON = python
VENV = venv
PIP = $(VENV)/Scripts/pip
UVICORN = $(VENV)/Scripts/uvicorn
PYTEST = $(VENV)/Scripts/pytest
PYINSTALLER = $(VENV)/Scripts/pyinstaller
APP = app.main:app
ACTIVATE_VENV = $(CURDIR)/$(VENV)/Scripts/Activate.ps1

# Create virtual environment
venv:
	@if not exist $(VENV) $(PYTHON) -m venv $(VENV)

# Open a PowerShell session with the virtual environment activated
activate: venv
	powershell -NoExit -ExecutionPolicy RemoteSigned -Command "& '$(ACTIVATE_VENV)'"

# Install dependencies
install: venv
	$(PIP) install -r requirements.txt

# Run production server
run:
	$(UVICORN) $(APP) --host 0.0.0.0 --port 51441

# Build standalone Python backend for Tauri bundling
build-release: install
	if exist dist\purifyt rmdir /s /q dist\purifyt
	if exist dist\purifyt-server.exe del /q dist\purifyt-server.exe
	$(PYINSTALLER) purifyt.spec --clean --noconfirm

# Run development server with hot reload
dev:
	$(UVICORN) $(APP) --reload --host 127.0.0.1 --port 51441

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
