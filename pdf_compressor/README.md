# 📄 Local PDF Compressor Web App

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg?style=flat&logo=python&logoColor=white)](https://python.org)
[![Framework](https://img.shields.io/badge/Framework-Flask-black.svg?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com)
[![Privacy](https://img.shields.io/badge/Privacy-100%25%20Local%20%26%20Zero%20Leakage-success.svg?style=flat)]()
[![Author](https://img.shields.io/badge/Author-Chandan%20Singh-blueviolet.svg?style=flat)](https://github.com/SCHANDAN996)

A clean, responsive, and privacy-focused **Flask Web Application** designed to compress, optimize, and reduce PDF document sizes locally without sending any data to third-party cloud servers.

---

## ✨ Features & Architecture

* 🔒 **100% Private & Air-Gapped Safe:** All PDF parsing, image re-compression, and stream optimization execute on `localhost`. Zero network data transmission.
* ⚡ **Multi-Level Compression Modes:**
  * **Extreme (Low DPI):** Drastic file reduction for portals with <100KB upload limits.
  * **Balanced (Recommended):** Optimal balance between visual crispness and file size reduction (50%–80% savings).
  * **High Quality (Retain Clarity):** Removes uncompressed streams and font bloat while preserving 300 DPI text.
* 📊 **Instant File Size Comparison:** Real-time before/after size difference indicators in MB and percentage.
* 🖥️ **Modern Drag-and-Drop Interface:** Built with clean HTML5/CSS3 glassmorphism styling.

---

## 🛠️ Tech Stack

* **Backend Engine:** Python 3, Flask, PyMuPDF (`fitz`), `pypdf`
* **Frontend UI:** Modern Vanilla CSS3, Responsive Flexbox/Grid, Vanilla JavaScript

---

## 🚀 Quickstart Guide

### 1. Clone & Install Dependencies
```bash
# Install required Python packages
pip install flask pymupdf pypdf
```

### 2. Run Application
```bash
python app.py
```

### 3. Open in Browser
Navigate to [http://127.0.0.1:5000](http://127.0.0.1:5000) and compress your documents instantly.

---

## 👤 Author & Maintainer
* **Chandan Singh** — [@SCHANDAN996](https://github.com/SCHANDAN996)
* 📬 **Contact:** [all.chandansingh@gmail.com](mailto:all.chandansingh@gmail.com)
