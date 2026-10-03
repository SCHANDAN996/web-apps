import sqlite3
import json

pyq_weightage = {
    "topicEn": "Percentage",
    "topicHi": "प्रतिशत",
    "totalQuestionsPastYears": 35,
    "weightagePercent": "20% (Core Topic)",
    "subConcepts": [
        {"nameHi": "मूल प्रतिशत निकालना", "nameEn": "Basic Calculation", "frequency": 7, "percent": 20},
        {"nameHi": "तुलनात्मक प्रतिशत", "nameEn": "Comparative %", "frequency": 6, "percent": 17},
        {"nameHi": "क्रमिक प्रतिशत", "nameEn": "Successive %", "frequency": 5, "percent": 14},
        {"nameHi": "चुनाव आधारित", "nameEn": "Election-based", "frequency": 4, "percent": 11},
        {"nameHi": "आय-व्यय/बचत", "nameEn": "Income-Exp./Savings", "frequency": 4, "percent": 11},
        {"nameHi": "जनसंख्या वृद्धि/मिश्रण", "nameEn": "Population/Mixture", "frequency": 3, "percent": 9},
        {"nameHi": "पासिंग मार्क्स/अंक", "nameEn": "Passing Marks", "frequency": 3, "percent": 9},
        {"nameHi": "वेन आरेख (फेल/पास)", "nameEn": "Venn Diagram", "frequency": 2, "percent": 6},
        {"nameHi": "अन्य", "nameEn": "Miscellaneous", "frequency": 1, "percent": 3}
    ]
}

pyq_inline = [
    {
        "exam": "SSC CGL", "year": 2020,
        "questionHi": "एक संख्या का 15%, 60 है। उस संख्या का 40% कितना होगा?",
        "questionEn": "15% of a number is 60. What is 40% of that number?",
        "options": ["120", "160", "200", "240"],
        "correct": "B",
        "explanationHi": "कुल संख्या = (60 / 15) × 100 = 400। 400 का 40% = (400 × 40) / 100 = 160।",
        "explanationEn": "Total number = (60 / 15) × 100 = 400. 40% of 400 = (400 × 40) / 100 = 160."
    },
    {
        "exam": "SSC CGL", "year": 2019,
        "questionHi": "एक परीक्षा में 30% छात्र गणित में फेल हुए और 25% अंग्रेजी में फेल हुए। यदि 15% दोनों में फेल हुए, तो कितने प्रतिशत छात्र दोनों विषयों में पास हुए?",
        "questionEn": "In an exam, 30% students failed in Maths, 25% failed in English and 15% failed in both. What percent of students passed in both subjects?",
        "options": ["40%", "50%", "60%", "70%"],
        "correct": "C",
        "explanationHi": "कुल फेल = (30+25-15)% = 40%। अतः दोनों में पास = 100% - 40% = 60%।",
        "explanationEn": "Total failed = (30+25-15)% = 40%. So passed in both = 100% - 40% = 60%."
    },
    {
        "exam": "SSC CHSL", "year": 2018,
        "questionHi": "यदि A की आय B से 25% अधिक है, तो B की आय A से कितने प्रतिशत कम है?",
        "questionEn": "If A's income is 25% more than B's, by what percent is B's income less than A's?",
        "options": ["20%", "25%", "16.67%", "30%"],
        "correct": "A",
        "explanationHi": "B = 100, A = 125। अंतर = 25। प्रतिशत कमी = (25/125)×100 = 20%।",
        "explanationEn": "B = 100, A = 125. Difference = 25. Percent less = (25/125)×100 = 20%."
    },
    {
        "exam": "IBPS PO", "year": 2021,
        "questionHi": "एक वस्तु का मूल्य 20% बढ़ाकर फिर 10% घटा दिया गया। शुद्ध प्रतिशत परिवर्तन ज्ञात करें।",
        "questionEn": "A price is increased by 20% and then decreased by 10%. Find the net percentage change.",
        "options": ["8% वृद्धि", "8% कमी", "10% वृद्धि", "10% कमी"],
        "correct": "A",
        "explanationHi": "20+(-10) + (20×-10)/100 = 10 - 2 = +8% वृद्धि।",
        "explanationEn": "20+(-10) + (20×-10)/100 = 10 - 2 = +8% increase."
    },
    {
        "exam": "SBI PO", "year": 2020,
        "questionHi": "एक शहर की जनसंख्या 8000 है। पहले वर्ष 10% वृद्धि और दूसरे वर्ष 20% वृद्धि होती है। दो वर्ष बाद जनसंख्या क्या होगी?",
        "questionEn": "A town's population is 8000. It increases by 10% in the first year and 20% in the second year. What is the population after two years?",
        "options": ["10400", "10560", "10800", "11000"],
        "correct": "B",
        "explanationHi": "8000 × (110/100) × (120/100) = 8000 × 1.1 × 1.2 = 10560।",
        "explanationEn": "8000 × (110/100) × (120/100) = 8000 × 1.1 × 1.2 = 10560."
    }
]

conn = sqlite3.connect('study_station.db')
c = conn.cursor()
c.execute(
    "UPDATE book_chapter SET pyq_weightage = ?, pyq_inline = ? WHERE id = 4", 
    (json.dumps(pyq_weightage, ensure_ascii=False), json.dumps(pyq_inline, ensure_ascii=False))
)
conn.commit()
conn.close()
print("PYQ phase B assets pushed successfully!")
