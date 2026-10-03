# Job Scraper को हर 3 घंटे अपने-आप चलाना (Windows Task Scheduler)

एक बार यह command **Administrator PowerShell** में चलाएँ:

```powershell
schtasks /Create /TN "StudyStation Job Update" /TR "\"C:\Users\Admin\Desktop\my project\study_station\backend-server\run_job_update.bat\"" /SC HOURLY /MO 3 /F
```

- हर 3 घंटे में `job_scraper.py run` चलेगा
- नई jobs मिलने पर website अपने-आप rebuild होगी
- Log यहाँ बनेगा: `backend-server/job_scraper.log`

## बंद करना हो तो:
```powershell
schtasks /Delete /TN "StudyStation Job Update" /F
```

## Manual commands:
```powershell
cd "C:\Users\Admin\Desktop\my project\study_station\backend-server"
venv\Scripts\python.exe job_scraper.py run       # नई jobs लाओ
venv\Scripts\python.exe job_scraper.py backfill  # पुरानी jobs की असली details भरो
venv\Scripts\python.exe job_scraper.py clean     # (हो चुका) नकली data हटाओ
venv\Scripts\python.exe build_website.py         # website rebuild
```

> **Note:** जब backend cloud पर deploy होगा (Phase 4), वहाँ यही काम cron job से होगा और यह local scheduler हटा दिया जाएगा।
