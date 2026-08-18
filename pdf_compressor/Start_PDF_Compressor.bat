@echo off
echo Starting PDFKaro Compressor Application...
echo Please wait while we check dependencies.

python -c "import pip" >nul 2>&1
if %errorlevel% neq 0 (
    echo Python or pip is not installed. Please install Python and add it to PATH.
    pause
    exit /b
)

echo Installing required packages (PyMuPDF, Flask, Pillow)...
pip install -q PyMuPDF Flask Pillow Werkzeug flask-cors

echo Starting Server...
python app.py

pause
