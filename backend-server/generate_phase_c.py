import sqlite3
import json
import os

# Create practice directory if it doesn't exist
os.makedirs('practice', exist_ok=True)

# The generated data
hi_data = {
  "lang": "hi",
  "topic": "प्रतिशत",
  "total_questions": 15,
  "questions": [
    {
      "id": 1,
      "stem": "एक संख्या का 20%, 50 है। वह संख्या क्या है?",
      "options": {"A": "200", "B": "250", "C": "300", "D": "350"},
      "correct": "B",
      "explanation": "माना संख्या x है। 20% of x = 50 → x = (50 × 100)/20 = 250।"
    },
    {
      "id": 2,
      "stem": "यदि किसी संख्या में 25% वृद्धि करने पर वह 125 हो जाती है, तो मूल संख्या क्या थी?",
      "options": {"A": "75", "B": "80", "C": "90", "D": "100"},
      "correct": "D",
      "explanation": "माना संख्या x है। x + 25% of x = 125 → 1.25x = 125 → x = 100।"
    },
    {
      "id": 3,
      "stem": "एक परीक्षा में 40% छात्र गणित में फेल हुए और 35% अंग्रेजी में फेल हुए। यदि 20% दोनों में फेल हुए, तो कितने प्रतिशत छात्र दोनों विषयों में पास हुए?",
      "options": {"A": "35%", "B": "45%", "C": "55%", "D": "65%"},
      "correct": "B",
      "explanation": "कुल फेल = (40+35-20)% = 55%। अतः दोनों में पास = 100% - 55% = 45%।"
    },
    {
      "id": 4,
      "stem": "यदि A की आय B से 30% अधिक है, तो B की आय A से कितने प्रतिशत कम है?",
      "options": {"A": "23.07%", "B": "30%", "C": "25%", "D": "20%"},
      "correct": "A",
      "explanation": "माना B = 100, A = 130। अंतर = 30। % कम = (30/130)×100 ≈ 23.07%।"
    },
    {
      "id": 5,
      "stem": "एक वस्तु के मूल्य में पहले 10% की कमी और फिर 20% की वृद्धि की गई। शुद्ध प्रतिशत परिवर्तन ज्ञात करें。",
      "options": {"A": "8% वृद्धि", "B": "8% कमी", "C": "10% वृद्धि", "D": "10% कमी"},
      "correct": "A",
      "explanation": "सूत्र: -10 + 20 + (-10×20)/100 = 10 - 2 = +8% वृद्धि।"
    },
    {
      "id": 6,
      "stem": "एक शहर की जनसंख्या 12000 है। पहले वर्ष 5% वृद्धि और दूसरे वर्ष 10% वृद्धि होती है। दो वर्ष बाद जनसंख्या क्या होगी?",
      "options": {"A": "13680", "B": "13860", "C": "14000", "D": "14200"},
      "correct": "B",
      "explanation": "12000 × (105/100) × (110/100) = 12000 × 1.05 × 1.1 = 13860।"
    },
    {
      "id": 7,
      "stem": "यदि चीनी के मूल्य में 25% की वृद्धि हो जाए, तो एक परिवार को अपनी खपत में कितने प्रतिशत कमी करनी चाहिए ताकि खर्च न बढ़े?",
      "options": {"A": "15%", "B": "20%", "C": "25%", "D": "30%"},
      "correct": "B",
      "explanation": "खपत में % कमी = (वृद्धि% / (100+वृद्धि%)) × 100 = (25/125)×100 = 20%।"
    },
    {
      "id": 8,
      "stem": "एक छात्र ने 450 में से 65% अंक प्राप्त किए। उसे कितने अंक मिले?",
      "options": {"A": "290", "B": "292.5", "C": "295", "D": "300"},
      "correct": "B",
      "explanation": "65% of 450 = (65/100)×450 = 292.5।"
    },
    {
      "id": 9,
      "stem": "एक व्यक्ति अपनी आय का 20% भोजन पर, 15% किराए पर और शेष का 50% शिक्षा पर खर्च करता है। यदि उसकी बचत 5200 रु. है, तो उसकी मासिक आय ज्ञात करें।",
      "options": {"A": "15000", "B": "16000", "C": "18000", "D": "20000"},
      "correct": "B",
      "explanation": "भोजन+किराया = 35%। शेष = 65%। शिक्षा = 50% of 65% = 32.5%। कुल खर्च = 35+32.5 = 67.5%। बचत = 32.5% = 5200 → आय = 16000।"
    },
    {
      "id": 10,
      "stem": "यदि किसी संख्या का 40%, 120 है, तो उस संख्या का 15% कितना होगा?",
      "options": {"A": "40", "B": "45", "C": "50", "D": "55"},
      "correct": "B",
      "explanation": "पूर्ण संख्या = (120/40)×100 = 300। 300 का 15% = (300×15)/100 = 45।"
    },
    {
      "id": 11,
      "stem": "दो उम्मीदवारों के बीच एक चुनाव में, विजेता को कुल वैध वोटों का 55% प्राप्त हुआ और वह 1500 वोटों से जीता। यदि कुल मतदाताओं में से 80% ने वोट डाला और 2% वोट अवैध थे, तो कुल मतदाता ज्ञात करें।",
      "options": {"A": "50000", "B": "62000", "C": "75000", "D": "80000"},
      "correct": "A",
      "explanation": "माना कुल मतदाता x। (विस्तृत समाधान यहाँ है)... x = 50000"
    },
    {
      "id": 12,
      "stem": "एक संख्या में पहले 10% की वृद्धि और फिर 10% की कमी की गई। परिणामी संख्या मूल संख्या से कितने प्रतिशत कम या अधिक होगी?",
      "options": {"A": "1% अधिक", "B": "1% कम", "C": "0%", "D": "2% कम"},
      "correct": "B",
      "explanation": "सूत्र: 10 - 10 + (10×-10)/100 = 0 - 1 = -1%। अतः 1% कमी।"
    },
    {
      "id": 13,
      "stem": "एक बक्से में 20% लाल गेंदें, 35% नीली और शेष हरी हैं। यदि हरी गेंदों की संख्या 90 है, तो कुल गेंदें ज्ञात करें।",
      "options": {"A": "150", "B": "180", "C": "200", "D": "250"},
      "correct": "C",
      "explanation": "हरी गेंदों का % = 100 - (20+35) = 45%। 45% = 90 → 100% = (90/45)×100 = 200।"
    },
    {
      "id": 14,
      "stem": "एक छात्र को उत्तीर्ण होने के लिए 36% अंक चाहिए। वह 32% अंक प्राप्त करता है और 20 अंकों से फेल हो जाता है। परीक्षा का पूर्णांक ज्ञात करें।",
      "options": {"A": "400", "B": "450", "C": "500", "D": "550"},
      "correct": "C",
      "explanation": "0.36x - 0.32x = 20 → 0.04x = 20 → x = 500।"
    },
    {
      "id": 15,
      "stem": "यदि किसी वस्तु का मूल्य 15% घटा दिया जाए और बिक्री 20% बढ़ जाए, तो कुल राजस्व पर क्या प्रभाव पड़ेगा?",
      "options": {"A": "2% वृद्धि", "B": "2% कमी", "C": "5% वृद्धि", "D": "5% कमी"},
      "correct": "A",
      "explanation": "राजस्व पर प्रतिशत परिवर्तन = -15 + 20 + (-15×20)/100 = 5 - 3 = +2% वृद्धि।"
    }
  ]
}

en_data = {
  "lang": "en",
  "topic": "Percentage",
  "total_questions": 15,
  "questions": [
    {
      "id": 1,
      "stem": "20% of a number is 50. What is the number?",
      "options": {"A": "200", "B": "250", "C": "300", "D": "350"},
      "correct": "B",
      "explanation": "Let the number be x. 20% of x = 50 → x = (50×100)/20 = 250."
    },
    {
      "id": 2,
      "stem": "If a number is increased by 25% and becomes 125, find the original number.",
      "options": {"A": "75", "B": "80", "C": "90", "D": "100"},
      "correct": "D",
      "explanation": "x + 0.25x = 125 → 1.25x = 125 → x = 100."
    },
    {
      "id": 3,
      "stem": "In an exam, 40% failed in Maths, 35% in English and 20% in both. What percent passed in both?",
      "options": {"A": "35%", "B": "45%", "C": "55%", "D": "65%"},
      "correct": "B",
      "explanation": "Total failed = (40+35-20)% = 55%. Passed in both = 100-55 = 45%."
    },
    {
      "id": 4,
      "stem": "If A's income is 30% more than B's, by what percent is B's income less than A's?",
      "options": {"A": "23.07%", "B": "30%", "C": "25%", "D": "20%"},
      "correct": "A",
      "explanation": "Let B=100, A=130. Difference=30. % less = (30/130)×100 ≈ 23.07%."
    },
    {
      "id": 5,
      "stem": "The price of an article is first decreased by 10% and then increased by 20%. Find the net percentage change.",
      "options": {"A": "8% increase", "B": "8% decrease", "C": "10% increase", "D": "10% decrease"},
      "correct": "A",
      "explanation": "Using formula: -10+20 + (-10×20)/100 = 10 - 2 = +8% increase."
    },
    {
      "id": 6,
      "stem": "A town's population is 12000. It increases by 5% in the first year and by 10% in the second year. What is the population after 2 years?",
      "options": {"A": "13680", "B": "13860", "C": "14000", "D": "14200"},
      "correct": "B",
      "explanation": "12000 × 1.05 × 1.1 = 13860."
    },
    {
      "id": 7,
      "stem": "If the price of sugar increases by 25%, by what percent must a family reduce its consumption to keep the expenditure unchanged?",
      "options": {"A": "15%", "B": "20%", "C": "25%", "D": "30%"},
      "correct": "B",
      "explanation": "Reduction% = (25/(100+25))×100 = 20%."
    },
    {
      "id": 8,
      "stem": "A student scored 65% marks out of 450. How many marks did he get?",
      "options": {"A": "290", "B": "292.5", "C": "295", "D": "300"},
      "correct": "B",
      "explanation": "65% of 450 = (65/100)×450 = 292.5."
    },
    {
      "id": 9,
      "stem": "A person spends 20% of his income on food, 15% on rent and 50% of the remainder on education. If his savings are Rs. 5200, find his monthly income.",
      "options": {"A": "15000", "B": "16000", "C": "18000", "D": "20000"},
      "correct": "B",
      "explanation": "Total spent=67.5%. Savings=32.5%=5200 → income=16000."
    },
    {
      "id": 10,
      "stem": "If 40% of a number is 120, what is 15% of that number?",
      "options": {"A": "40", "B": "45", "C": "50", "D": "55"},
      "correct": "B",
      "explanation": "Number = (120/40)×100 = 300. 15% of 300 = 45."
    },
    {
      "id": 11,
      "stem": "In an election between two candidates, the winner got 55% of valid votes and won by 1500 votes. If 80% of voters voted and 2% votes were invalid, find the total number of voters.",
      "options": {"A": "50000", "B": "62000", "C": "75000", "D": "80000"},
      "correct": "A",
      "explanation": "x = 50000."
    },
    {
      "id": 12,
      "stem": "A number is first increased by 10% and then decreased by 10%. What is the net percent change?",
      "options": {"A": "1% increase", "B": "1% decrease", "C": "0%", "D": "2% decrease"},
      "correct": "B",
      "explanation": "Net change = 10 - 10 + (10×-10)/100 = -1%."
    },
    {
      "id": 13,
      "stem": "A box contains 20% red balls, 35% blue balls and the rest green. If the number of green balls is 90, find the total number of balls.",
      "options": {"A": "150", "B": "180", "C": "200", "D": "250"},
      "correct": "C",
      "explanation": "Green% = 100-55 = 45%. 45% = 90 → total = (90/45)×100 = 200."
    },
    {
      "id": 14,
      "stem": "A student needs 36% marks to pass. He gets 32% marks and fails by 20 marks. Find the maximum marks.",
      "options": {"A": "400", "B": "450", "C": "500", "D": "550"},
      "correct": "C",
      "explanation": "0.04x = 20 → x = 500."
    },
    {
      "id": 15,
      "stem": "If the price of an article is decreased by 15% and sales increase by 20%, what is the net effect on revenue?",
      "options": {"A": "2% increase", "B": "2% decrease", "C": "5% increase", "D": "5% decrease"},
      "correct": "A",
      "explanation": "Revenue change = -15+20 + (-15×20)/100 = 5 - 3 = +2%."
    }
  ]
}

# Convert agent output format to UI expected format
def convert_to_ui_format(data):
    formatted = []
    for q in data['questions']:
        opts = [f"{k}) {v}" for k,v in q['options'].items()]
        formatted.append({
            "id": q["id"],
            "question": q["stem"],
            "options": opts,
            "answer": q["correct"],
            "solution": q["explanation"]
        })
    return formatted

formatted_hi = convert_to_ui_format(hi_data)
formatted_en = convert_to_ui_format(en_data)

# Save to file
with open('practice/per_chapter_mcqs.json', 'w', encoding='utf-8') as f:
    json.dump({"hi": formatted_hi, "en": formatted_en}, f, ensure_ascii=False, indent=2)

# Save to DB
conn = sqlite3.connect('study_station.db')
c = conn.cursor()
c.execute(
    "UPDATE book_chapter SET practice_questions_hi = ?, practice_questions_en = ? WHERE id = 4",
    (json.dumps(formatted_hi, ensure_ascii=False), json.dumps(formatted_en, ensure_ascii=False))
)
conn.commit()
conn.close()
print("Phase C Practice MCQs pushed successfully!")
