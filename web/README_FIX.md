# Flask App Fix Summary

## Problem
The Flask app wouldn't run due to Python import errors. The core issue was that modules in the OntServe package were using relative imports (`from ..storage.base import ...`) which caused ImportError when Flask tried to load them.

## Solution Applied
Changed all relative imports to absolute imports in:
- `OntServe/core/ontology_manager.py`
- `OntServe/importers/prov_importer.py` 
- `OntServe/importers/bfo_importer.py`

## How to Run the App

### Method 1: Direct Python Execution (Recommended for development)
```bash
cd OntServe/web
python app.py
```
Note: Port 8000 is currently in use. You can either:
- Stop the process using port 8000, or
- Change the port in `config.py`

### Method 2: Flask CLI with proper environment
```bash
cd OntServe/web
export PYTHONPATH=/home/chris/onto/OntServe:$PYTHONPATH
export FLASK_APP=app.py
export FLASK_ENV=development
flask run --host=0.0.0.0 --port=5001
```

### Method 3: Using VSCode Launch Configuration
The VSCode launch configuration should work now, but you may need to ensure the Python interpreter is set correctly:
1. Open Command Palette (Ctrl+Shift+P)
2. Type "Python: Select Interpreter"
3. Choose the Python interpreter from your virtual environment

## Configuration Notes

### Current Settings (config.py)
- Default Port: 8000 (currently in use, consider changing to 5001)
- Database: PostgreSQL on localhost:5434
- Debug Mode: Enabled in development

### To Change Port
Edit `OntServe/web/config.py`:
```python
PORT = 5001  # Change from 8000
```

## Alternative: Simple Run Script
Create a simple run script:
```bash
#!/bin/bash
cd /home/chris/onto/OntServe/web
export PYTHONPATH=/home/chris/onto/OntServe:$PYTHONPATH
python app.py
```

## Troubleshooting

If you still encounter import issues:
1. Ensure all dependencies are installed: `pip install -r requirements.txt`
2. Check that the PYTHONPATH includes the OntServe directory
3. Verify the database is running on port 5434
4. Check for any processes using port 8000: `lsof -i :8000`
