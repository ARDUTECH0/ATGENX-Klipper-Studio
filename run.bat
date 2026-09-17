@echo off
cd /d "%~dp0"
python -c "import PySide6" 2>nul || python -m pip install -r requirements.txt
where pythonw >nul 2>nul && (start "" pythonw -m studio %*) || python -m studio %*
