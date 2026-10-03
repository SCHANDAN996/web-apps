@echo off
REM Study Station — job update runner (for Windows Task Scheduler)
REM Fetches new jobs, extracts real details, rebuilds the static site.
cd /d "%~dp0"
venv\Scripts\python.exe job_scraper.py run >> job_scraper.log 2>&1
