# 🤖 Pro-AI Trading Engine v3.0 (Institutional Grade)

यह एक **Autonomous Trading System** है जो Deep Learning (LSTM + Attention Mechanism) का उपयोग करके स्टॉक मार्केट के पैटर्न्स को सीखता है, लाइव चार्ट्स को एनालाइज करता है और बिना किसी मानवीय हस्तक्षेप के ट्रेड्स को एग्जीक्यूट करता है।

---

## 🚀 मुख्य विशेषताएं (Key Features)

* **Self-Training Brain:** ऐतिहासिक डेटा (Historical Data) पर आधारित खुद को ट्रेन करने वाला AI मॉडल।
* **Attention-based LSTM:** मार्केट की महत्वपूर्ण घटनाओं पर ध्यान केंद्रित करने के लिए आधुनिक न्यूरल नेटवर्क।
* **Multi-Timeframe Analysis:** 1-घंटे का ट्रेंड और 5-मिनट की एंट्री का सटीक मिलान।
* **Regime Detection (ADX):** साइडवेज मार्केट में गलत ट्रेडों से बचने के लिए स्मार्ट फिल्टर।
* **Risk Management:** डायनामिक स्टॉप-लॉस, ट्रेलिंग स्टॉप-लॉस और डेली लॉस लिमिट।
* **Remote Control:** टेलीग्राम के ज़रिए लाइव अलर्ट्स और "Emergency Kill-Switch"।
* **Professional Dashboard:** Streamlit पर आधारित लाइव विजुअल मॉनिटरिंग।

---

## 📂 प्रोजेक्ट का ढांचा (Folder Structure)

```text
Trading_AI_Project/
├── config/             # API क्रेडेंशियल्स और सेटिंग्स
├── data/               # Raw और Processed डेटा (CSV/SQL)
├── models/             # ट्रेन किए हुए .h5 मॉडल्स
├── logs/               # लाइव ट्रेडिंग और एरर लॉग्स
├── src/                # कोर सोर्स कोड (Modules)
│   ├── connector.py    # Shoonya/Dhan API कनेक्शन
│   ├── brain.py        # Attention + LSTM AI Architecture
│   ├── risk_manager.py # कैपिटल प्रोटेक्शन लॉजिक
│   ├── executor.py     # स्मार्ट ऑर्डर एग्जीक्यूशन
│   ├── notifier.py     # टेलीग्राम अलर्ट्स
│   └── database.py     # SQLite डेटाबेस मैनेजर
├── main.py             # बॉट को शुरू करने वाला मेन इंजन
├── dashboard.py        # लाइव विजुअल डैशबोर्ड (Streamlit)
├── train_model.py      # AI ट्रेनिंग स्क्रिप्ट
├── data_downloader.py  # डेटा डाउनलोडर
└── kill_switch.py      # एमरजेंसी स्टॉप स्क्रिप्ट
```

---

## 🛠️ इंस्टॉलेशन और सेटअप (Installation)

### 1. लाइब्रेरीज़ इंस्टॉल करें:

```bash
pip install -r requirements.txt
```

### 2. कॉन्फ़िगरेशन:

`config/credentials.env` फाइल बनाएं और अपनी डिटेल्स डालें:

```env
USER_ID=your_id
PASSWORD=your_pass
API_KEY=your_key
TOTP_SECRET=your_totp
TELEGRAM_TOKEN=your_token
TELEGRAM_CHAT_ID=your_id
ENVIRONMENT=PAPER_TRADING
MAX_DAILY_LOSS=5000
```

---

## 📈 इस्तेमाल कैसे करें (Usage)

1. **डेटा डाउनलोड करें:**
`python data_downloader.py`
2. **AI को ट्रेन करें:**
`python train_model.py`
3. **बॉट चालू करें (Local):**
`python main.py`
4. **डैशबोर्ड देखें:**
`streamlit run dashboard.py`

---

## ☁️ VPS पर डिप्लॉयमेंट (Deployment)

बॉट को 24/7 चलाने के लिए **PM2** का उपयोग करें। आप `start_bot.sh` स्क्रिप्ट का उपयोग कर सकते हैं:

```bash
chmod +x start_bot.sh
./start_bot.sh
```

---

## ⚠️ चेतावनी (Risk Disclaimer)

**ट्रेडिंग में जोखिम शामिल है।** यह बॉट शिक्षा और रिसर्च के उद्देश्य से बनाया गया है। असली पैसा लगाने से पहले कम से कम 100 पेपर ट्रेड्स (Paper Trades) ज़रूर करें। डेवलपर किसी भी वित्तीय नुकसान के लिए ज़िम्मेदार नहीं होगा।

---

## 👨💻 डेवलपर

* **नाम:** Antigravity
* **प्रोफेशन:** AI Agent
