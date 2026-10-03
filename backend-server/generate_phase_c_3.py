import sqlite3
import json

new_hi = [
{
  "id": 31,
  "stem": "एक संख्या में पहले 20% और फिर 30% की वृद्धि की जाती है। कुल प्रतिशत वृद्धि कितनी हुई?",
  "options": {"A": "50%", "B": "56%", "C": "60%", "D": "55%"},
  "correct": "B",
  "explanation": "कुल वृद्धि = 20+30 + (20×30)/100 = 50 + 6 = 56%।"
},
{
  "id": 32,
  "stem": "एक संख्या का 40%, 180 है। उस संख्या का 75% कितना होगा?",
  "options": {"A": "300", "B": "337.5", "C": "350", "D": "375"},
  "correct": "B",
  "explanation": "संख्या = (180/40)×100 = 450। 450 का 75% = (75/100)×450 = 337.5।"
},
{
  "id": 33,
  "stem": "यदि किसी वस्तु के मूल्य में 40% वृद्धि हो जाए, तो उपभोक्ता को अपनी खपत में कितने प्रतिशत कमी करनी चाहिए ताकि खर्च न बढ़े?",
  "options": {"A": "25%", "B": "28.57%", "C": "30%", "D": "40%"},
  "correct": "B",
  "explanation": "कमी% = (40/(100+40))×100 = (40/140)×100 ≈ 28.57%।"
},
{
  "id": 34,
  "stem": "एक छात्र ने 35% अंक प्राप्त किए और 40 अंकों से फेल हो गया। दूसरे छात्र ने 45% अंक प्राप्त किए और उसे उत्तीर्ण होने के लिए आवश्यक अंकों से 50 अंक अधिक मिले। पूर्णांक ज्ञात करें।",
  "options": {"A": "800", "B": "900", "C": "1000", "D": "700"},
  "correct": "B",
  "explanation": "माना पूर्णांक x। उत्तीर्णांक = 0.35x+40 = 0.45x-50 → 0.10x = 90 → x = 900।"
},
{
  "id": 35,
  "stem": "80 लीटर के मिश्रण में 60% दूध और शेष पानी है। मिश्रण में कितना पानी और मिलाया जाए कि पानी 50% हो जाए?",
  "options": {"A": "10 लीटर", "B": "12 लीटर", "C": "16 लीटर", "D": "20 लीटर"},
  "correct": "C",
  "explanation": "दूध = 60% of 80 = 48 लीटर, पानी = 32 लीटर। माना पानी मिलाया = w। (32+w)/(80+w) = 0.5 → 32+w = 40+0.5w → 0.5w = 8 → w = 16 लीटर।"
},
{
  "id": 36,
  "stem": "एक कक्षा में लड़के और लड़कियों का अनुपात 4:5 है। कक्षा में लड़कों का प्रतिशत कितना है?",
  "options": {"A": "40%", "B": "44.44%", "C": "50%", "D": "55.55%"},
  "correct": "B",
  "explanation": "कुल भाग = 9। लड़के = (4/9)×100 ≈ 44.44%।"
},
{
  "id": 37,
  "stem": "एक संख्या में पहले 15% कमी और फिर 20% वृद्धि की जाती है। शुद्ध प्रतिशत परिवर्तन क्या है?",
  "options": {"A": "2% वृद्धि", "B": "2% कमी", "C": "5% वृद्धि", "D": "5% कमी"},
  "correct": "A",
  "explanation": "-15+20 + (-15×20)/100 = 5 - 3 = +2% वृद्धि।"
},
{
  "id": 38,
  "stem": "यदि एक संख्या का 10% और दूसरी संख्या का 20% जोड़ा जाए तो योग 50 आता है। यदि पहली संख्या 200 हो, तो दूसरी संख्या ज्ञात करें।",
  "options": {"A": "100", "B": "150", "C": "200", "D": "250"},
  "correct": "B",
  "explanation": "200 का 10% = 20। तो 20 + y का 20% = 50 → 0.2y = 30 → y = 150।"
},
{
  "id": 39,
  "stem": "एक शर्ट के मूल्य पर 20% छूट देने के बाद उसका मूल्य 640 रु. रह जाता है। उसका मूल मूल्य क्या था?",
  "options": {"A": "700 रु.", "B": "750 रु.", "C": "800 रु.", "D": "850 रु."},
  "correct": "C",
  "explanation": "मूल मूल्य का 80% = 640 → मूल मूल्य = 640/0.8 = 800 रु.।"
},
{
  "id": 40,
  "stem": "एक विद्यालय में 40% छात्राएँ हैं। यदि लड़कों की संख्या 480 हो, तो कुल छात्रों की संख्या ज्ञात करें।",
  "options": {"A": "700", "B": "750", "C": "800", "D": "850"},
  "correct": "C",
  "explanation": "लड़के = 60% = 480 → कुल = 480/0.6 = 800।"
},
{
  "id": 41,
  "stem": "मूल्य में 15% वृद्धि होने के कारण एक व्यक्ति 200 रु. में 3 किग्रा चीनी कम खरीद पाता है। चीनी का मूल मूल्य प्रति किग्रा ज्ञात करें।",
  "options": {"A": "8 रु.", "B": "10 रु.", "C": "12 रु.", "D": "15 रु."},
  "correct": "B",
  "explanation": "मान लीजिए मूल मूल्य x रु./किग्रा। 200/x - 200/(1.15x) = 3 → (200/x)(0.15/1.15) = 3 → x = 10 रु.। (मानक उत्तर)"
},
{
  "id": 42,
  "stem": "किसी संख्या को 5 से गुणा करने के बजाय गलती से 5 से भाग दिया गया। परिणाम में कितने प्रतिशत त्रुटि होगी?",
  "options": {"A": "96%", "B": "90%", "C": "80%", "D": "84%"},
  "correct": "A",
  "explanation": "माना संख्या x। सही परिणाम = 5x, गलत = x/5। त्रुटि = 5x - x/5 = (24x/5)। % त्रुटि = (त्रुटि/सही)×100 = (24x/5)/(5x)×100 = (24/25)×100 = 96%।"
},
{
  "id": 43,
  "stem": "यदि किसी वृत्त की त्रिज्या में 50% वृद्धि कर दी जाए, तो उसके क्षेत्रफल में कितने प्रतिशत वृद्धि होगी?",
  "options": {"A": "100%", "B": "125%", "C": "150%", "D": "200%"},
  "correct": "B",
  "explanation": "क्षेत्रफल ∝ त्रिज्या²। % वृद्धि = 50+50 + (50×50)/100 = 100+25 = 125%।"
},
{
  "id": 44,
  "stem": "एक व्यक्ति अपनी आय का 10% दान करता है, शेष का 20% भोजन पर और फिर शेष का 25% किराए पर खर्च करता है। यदि उसके पास 4320 रु. बचते हैं, तो उसकी आय क्या है?",
  "options": {"A": "8000", "B": "10000", "C": "12000", "D": "15000"},
  "correct": "A",
  "explanation": "माना आय x। दान के बाद: 0.9x। भोजन के बाद: 0.8×0.9x = 0.72x। किराए के बाद: 0.75×0.72x = 0.54x। 0.54x = 4320 → x = 8000।"
},
{
  "id": 45,
  "stem": "एक शहर की जनसंख्या में पहले वर्ष 10% वृद्धि, दूसरे वर्ष 10% कमी और तीसरे वर्ष 10% वृद्धि हुई। कुल प्रतिशत परिवर्तन क्या है?",
  "options": {"A": "8.9% वृद्धि", "B": "9.0% वृद्धि", "C": "8.9% कमी", "D": "10% वृद्धि"},
  "correct": "A",
  "explanation": "पहले दो वर्षों का शुद्ध प्रभाव = 10-10 + (10×-10)/100 = -1%। फिर तीसरे वर्ष +10%: नया शुद्ध = -1+10 + (-1×10)/100 = 9 - 0.1 = 8.9% वृद्धि।"
}
]

new_en = [
{
  "id": 31,
  "stem": "A number is increased by 20% and then again by 30%. What is the overall percentage increase?",
  "options": {"A": "50%", "B": "56%", "C": "60%", "D": "55%"},
  "correct": "B",
  "explanation": "Overall increase = 20+30 + (20×30)/100 = 50 + 6 = 56%."
},
{
  "id": 32,
  "stem": "40% of a number is 180. What is 75% of that number?",
  "options": {"A": "300", "B": "337.5", "C": "350", "D": "375"},
  "correct": "B",
  "explanation": "Number = (180/40)×100 = 450. 75% of 450 = (75/100)×450 = 337.5."
},
{
  "id": 33,
  "stem": "If the price of a commodity is increased by 40%, by how much percent must a consumer reduce his consumption to keep the expenditure unchanged?",
  "options": {"A": "25%", "B": "28.57%", "C": "30%", "D": "40%"},
  "correct": "B",
  "explanation": "Reduction% = (40/(100+40))×100 = (40/140)×100 ≈ 28.57%."
},
{
  "id": 34,
  "stem": "A student scored 35% marks and failed by 40 marks. Another student scored 45% marks and got 50 marks more than the passing marks. Find the maximum marks.",
  "options": {"A": "800", "B": "900", "C": "1000", "D": "700"},
  "correct": "B",
  "explanation": "Let max marks = x. Pass marks = 0.35x + 40 = 0.45x - 50 → 0.10x = 90 → x = 900."
},
{
  "id": 35,
  "stem": "In a mixture of 80 litres, milk is 60% and the rest is water. How much water should be added to make water 50% in the new mixture?",
  "options": {"A": "10 litres", "B": "12 litres", "C": "16 litres", "D": "20 litres"},
  "correct": "C",
  "explanation": "Water initially = 40% of 80 = 32 litres. Milk = 48 litres. To make water 50%, new total = 48/(50%) = 96 litres, water needed = 48 litres. So water to add = 48-32 = 16 litres."
},
{
  "id": 36,
  "stem": "The ratio of boys to girls in a class is 4:5. What percentage of the class are boys?",
  "options": {"A": "40%", "B": "44.44%", "C": "50%", "D": "55.55%"},
  "correct": "B",
  "explanation": "Total parts = 9. Boys = 4/9 × 100 ≈ 44.44%."
},
{
  "id": 37,
  "stem": "A number is decreased by 15% and then increased by 20%. What is the net percentage change?",
  "options": {"A": "2% increase", "B": "2% decrease", "C": "5% increase", "D": "5% decrease"},
  "correct": "A",
  "explanation": "-15+20 + (-15×20)/100 = 5 - 3 = +2% increase."
},
{
  "id": 38,
  "stem": "If 10% of a number is added to 20% of another number, the sum is 50. If the first number is 200, find the second number.",
  "options": {"A": "100", "B": "150", "C": "200", "D": "250"},
  "correct": "B",
  "explanation": "10% of 200 = 20. So 20 + 20% of y = 50 → 0.2y = 30 → y = 150."
},
{
  "id": 39,
  "stem": "The price of a shirt after a 20% discount is Rs. 640. What was its original price?",
  "options": {"A": "Rs. 700", "B": "Rs. 750", "C": "Rs. 800", "D": "Rs. 850"},
  "correct": "C",
  "explanation": "80% of original price = 640 → original price = 640/0.8 = 800."
},
{
  "id": 40,
  "stem": "In a school, 40% students are girls. If the number of boys is 480, find the total number of students.",
  "options": {"A": "700", "B": "750", "C": "800", "D": "850"},
  "correct": "C",
  "explanation": "Boys = 60% = 480 → Total = 480/0.6 = 800."
},
{
  "id": 41,
  "stem": "Due to a 15% increase in price, a person can buy 3 kg less sugar for Rs. 200. Find the original price per kg.",
  "options": {"A": "Rs. 8", "B": "Rs. 10", "C": "Rs. 12", "D": "Rs. 15"},
  "correct": "B",
  "explanation": "Let original price = p. Quantity before = 200/p. New price = 1.15p, new quantity = 200/(1.15p). Difference = 3 → 200/p - 200/(1.15p) = 3 → p = 10."
},
{
  "id": 42,
  "stem": "A number is mistakenly divided by 5 instead of multiplied by 5. What is the percentage error in the result?",
  "options": {"A": "96%", "B": "90%", "C": "80%", "D": "84%"},
  "correct": "A",
  "explanation": "Let number = x. Correct result = 5x. Wrong result = x/5. Error = 5x - x/5 = (24x/5). % error = (Error / Correct) × 100 = ((24x/5) / 5x) × 100 = 96%."
},
{
  "id": 43,
  "stem": "If the radius of a circle is increased by 50%, what is the percentage increase in its area?",
  "options": {"A": "100%", "B": "125%", "C": "150%", "D": "200%"},
  "correct": "B",
  "explanation": "Area ∝ radius^2. Increase% = 50+50 + (50×50)/100 = 100+25 = 125%."
},
{
  "id": 44,
  "stem": "A man donates 10% of his income to charity, spends 20% of the remaining on food and 25% of the remaining on rent. If he is left with Rs. 4320, what is his income?",
  "options": {"A": "8000", "B": "10000", "C": "12000", "D": "15000"},
  "correct": "A",
  "explanation": "Let income = x. After charity: 0.9x. After food: 0.8×0.9x = 0.72x. After rent: 0.75×0.72x = 0.54x. So 0.54x = 4320 → x = 8000."
},
{
  "id": 45,
  "stem": "The population of a city increased by 10% in the first year, decreased by 10% in the second year and again increased by 10% in the third year. What is the overall percentage change?",
  "options": {"A": "8.9% increase", "B": "9.0% increase", "C": "8.9% decrease", "D": "10% increase"},
  "correct": "A",
  "explanation": "Net change = 10 -10 + (10×-10)/100 = -1%, then again +10% on reduced base: overall = -1 +10 + (-1×10)/100 = 8.9% increase."
}
]

def convert(data):
    formatted = []
    for q in data:
        opts = [f"{k}) {v}" for k,v in q['options'].items()]
        formatted.append({
            "id": q["id"],
            "question": q["stem"],
            "options": opts,
            "answer": q["correct"],
            "solution": q["explanation"]
        })
    return formatted

conn = sqlite3.connect('study_station.db')
c = conn.cursor()
c.execute("SELECT practice_questions_hi, practice_questions_en FROM book_chapter WHERE id = 4")
row = c.fetchone()
hi = json.loads(row[0]) if row[0] else []
en = json.loads(row[1]) if row[1] else []

hi.extend(convert(new_hi))
en.extend(convert(new_en))

c.execute("UPDATE book_chapter SET practice_questions_hi = ?, practice_questions_en = ? WHERE id = 4", (json.dumps(hi, ensure_ascii=False), json.dumps(en, ensure_ascii=False)))
conn.commit()
conn.close()
print("Appended questions 31-45 successfully!")
