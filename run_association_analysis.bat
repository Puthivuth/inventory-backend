@echo off
REM Navigate to the backend directory
cd /d %~dp0

REM Activate the virtual environment
call env\Scripts\activate

REM Run the product association analysis
echo Starting Product Association Analysis...
python manage.py run_product_association --min-support=2 --min-confidence=1.0

echo Analysis Complete!
pause
