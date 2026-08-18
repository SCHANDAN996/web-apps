# 🤖 WhatsApp Scheduled Broadcast & Messaging Engine

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask-black.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Automation](https://img.shields.io/badge/Engine-PyWhatKit%20%7C%20Selenium-green.svg?style=flat)]()
[![Author](https://img.shields.io/badge/Author-Chandan%20Singh-blueviolet.svg?style=flat)](https://github.com/SCHANDAN996)

An automated Python and Flask Web application engineered for scheduling and broadcasting personalized WhatsApp text messages, documents, spreadsheets, and PDF reports to recipient contact lists.

---

## ✨ Core Features

* 📅 **Precise Schedule Dispatch:** Queue messages and file attachments to be sent at specific target hours and minutes.
* 📋 **Contact List Broadcast:** Import recipients directly or dispatch messages in batch sequence.
* 📎 **Multi-Format Attachment Support:** Automated transmission of PDF, DOCX, XLSX, and image files.
* 📜 **Dispatch History & Delivery Logs:** Real-time logging of sent, queued, and failed message dispatches via `history.json`.
* 🖥️ **Web Dashboard Interface:** Clean web UI to configure scheduling, compose messages, and monitor live task queues.

---

## 🛠️ Tech Stack

* **Backend Engine:** Python 3, Flask, PyWhatKit, Selenium Webdriver, APScheduler
* **Frontend UI:** HTML5, CSS3, JavaScript
* **Database / State:** Local JSON transaction log

---

## 🚀 Quickstart & Setup

### 1. Install Dependencies
```bash
pip install flask pywhatkit selenium schedule
```

### 2. Launch Automation Server
```bash
python app.py
```

### 3. Open Dashboard
Open [http://127.0.0.1:5000](http://127.0.0.1:5000) in your web browser. Make sure WhatsApp Web is logged in on your default browser.

---

## ⚠️ Important Usage Note
* This automation engine is built for legitimate notifications, student alerts, and client reports. Please respect WhatsApp's Terms of Service and avoid spamming.

---

## 👤 Author & Maintainer
* **Chandan Singh** — [@SCHANDAN996](https://github.com/SCHANDAN996)
* 📬 **Contact:** [all.chandansingh@gmail.com](mailto:all.chandansingh@gmail.com)
