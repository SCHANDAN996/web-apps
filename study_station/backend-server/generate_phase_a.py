import sqlite3
import json

mind_map = """
graph TD
    A[Percentage %] --> B(Basic Meaning)
    A --> C(Conversions)
    A --> D(Important Formulas)
    A --> E(Applications)
    
    B --> B1[Per 100]
    B --> B2[Fraction with denominator 100]
    
    C --> C1(Fraction to %)
    C1 --> C1a[Multiply by 100]
    C --> C2(% to Fraction)
    C2 --> C2a[Divide by 100]
    C --> C3(Decimal to %)
    C3 --> C3a[Move decimal right 2 places]
    
    D --> D1(Part/Total * 100)
    D --> D2(Net Successive Change)
    D2 --> D2a[a + b + ab/100]
    
    E --> E1(Profit/Loss)
    E --> E2(Simple/Compound Interest)
    E --> E3(Discount)
    E --> E4(Data Interpretation)
"""

flashcards_hi = [
    {"front": "प्रतिशत का शाब्दिक अर्थ क्या है?", "back": "प्रति 100 (Per Cent)। हर 100 के लिए एक हिस्सा।"},
    {"front": "भिन्न (Fraction) को प्रतिशत में कैसे बदलते हैं?", "back": "भिन्न को 100 से गुणा करके। (उदा: 1/4 × 100 = 25%)"},
    {"front": "प्रतिशत को भिन्न में कैसे बदलते हैं?", "back": "प्रतिशत को 100 से भाग देकर। (उदा: 20% = 20/100 = 1/5)"},
    {"front": "1/3 का प्रतिशत मान क्या है?", "back": "33.33% या 33 1/3%"},
    {"front": "1/8 का प्रतिशत मान क्या है?", "back": "12.5%"},
    {"front": "1/6 का प्रतिशत मान क्या है?", "back": "16.66% या 16 2/3%"},
    {"front": "क्रमिक प्रतिशत वृद्धि (Successive Increase) का सूत्र क्या है?", "back": "A + B + (A×B)/100"},
    {"front": "यदि आय 20% बढ़ जाए और फिर 20% घट जाए, तो शुद्ध परिवर्तन क्या होगा?", "back": "हमेशा कमी होगी। (x²/100)% = (400/100) = 4% की कमी।"},
    {"front": "'A का B%' किसके बराबर होता है?", "back": "'B का A%' के बराबर। (A×B)/100 = (B×A)/100"},
    {"front": "तुलना का आधार क्या होता है? (उदा: राम, श्याम से कितना कम कमाता है)", "back": "जिससे तुलना की जा रही है ('से' या 'than' के बाद वाला)। यहाँ 'श्याम' आधार (Denominator) होगा।"},
    {"front": "यदि X, Y से 25% अधिक है, तो Y, X से कितने % कम है?", "back": "(25 / 125) × 100 = 20% कम।"},
    {"front": "3/8 का प्रतिशत मान क्या है?", "back": "37.5%"},
    {"front": "4/5 का प्रतिशत मान क्या है?", "back": "80%"},
    {"front": "5/6 का प्रतिशत मान क्या है?", "back": "83.33%"},
    {"front": "यदि कोई संख्या 10% घटाई जाती है, तो वह मूल संख्या का कितना % बचती है?", "back": "90%"},
    {"front": "A, B का कितना प्रतिशत है, इसका सूत्र?", "back": "(A / B) × 100"},
    {"front": "जनसंख्या में R% वार्षिक वृद्धि हो, तो n वर्ष बाद जनसंख्या?", "back": "वर्तमान जनसंख्या × (1 + R/100)^n"},
    {"front": "जनसंख्या में R% वार्षिक वृद्धि हो, तो n वर्ष पूर्व जनसंख्या?", "back": "वर्तमान जनसंख्या / (1 + R/100)^n"},
    {"front": "मशीन के मूल्य में R% अवमूल्यन (Depreciation) हो, तो n वर्ष बाद मूल्य?", "back": "वर्तमान मूल्य × (1 - R/100)^n"},
    {"front": "रुको और सोचो (Pause & Think): क्या 50 का 10% और 10 का 50% समान है?", "back": "हाँ! दोनों 5 होते हैं। (A का B% = B का A%)"},
    {"front": "रुको और सोचो: 1/7 का % मान 14.28% है, तो 2/7 क्या होगा?", "back": "लगभग दोगुना! 28.56%"},
    {"front": "रुको और सोचो: यदि मूल्य 100 से 150 हो गया, तो वृद्धि % क्या है?", "back": "50% (वृद्धि 50, आधार 100: 50/100 * 100)"},
    {"front": "रुको और सोचो: यदि मूल्य 150 से 100 हो गया, तो कमी % क्या है?", "back": "33.33% (कमी 50, आधार 150: 50/150 * 100)"},
    {"front": "रुको और सोचो: प्रतिशत में 100% का क्या अर्थ है?", "back": "संपूर्ण या पूर्ण इकाई (Whole / 1)"}
]

flashcards_en = [
    {"front": "What is the literal meaning of Percentage?", "back": "Per 100 (Per Cent). A part for every 100."},
    {"front": "How do you convert a fraction to a percentage?", "back": "Multiply the fraction by 100. (e.g., 1/4 × 100 = 25%)"},
    {"front": "How do you convert a percentage to a fraction?", "back": "Divide the percentage by 100. (e.g., 20% = 20/100 = 1/5)"},
    {"front": "What is the percentage value of 1/3?", "back": "33.33% or 33 1/3%"},
    {"front": "What is the percentage value of 1/8?", "back": "12.5%"},
    {"front": "What is the percentage value of 1/6?", "back": "16.66% or 16 2/3%"},
    {"front": "What is the formula for successive percentage change?", "back": "A + B + (A×B)/100"},
    {"front": "If income increases by 20% and then decreases by 20%, what is the net change?", "back": "Always a decrease. (x²/100)% = (400/100) = 4% decrease."},
    {"front": "'A% of B' is equal to what?", "back": "'B% of A'. (A×B)/100 = (B×A)/100"},
    {"front": "What is the base of comparison? (e.g., How much less does Ram earn than Shyam?)", "back": "The value being compared against (after 'than' or 'to'). Here, 'Shyam' is the base (Denominator)."},
    {"front": "If X is 25% more than Y, by what % is Y less than X?", "back": "(25 / 125) × 100 = 20% less."},
    {"front": "What is the percentage value of 3/8?", "back": "37.5%"},
    {"front": "What is the percentage value of 4/5?", "back": "80%"},
    {"front": "What is the percentage value of 5/6?", "back": "83.33%"},
    {"front": "If a number is decreased by 10%, what % of the original number remains?", "back": "90%"},
    {"front": "Formula for: What % of B is A?", "back": "(A / B) × 100"},
    {"front": "If population grows at R% p.a., what is population after n years?", "back": "Current Pop × (1 + R/100)^n"},
    {"front": "If population grows at R% p.a., what was population n years ago?", "back": "Current Pop / (1 + R/100)^n"},
    {"front": "If machine depreciates at R% p.a., what is value after n years?", "back": "Current Value × (1 - R/100)^n"},
    {"front": "Pause & Think: Is 10% of 50 the same as 50% of 10?", "back": "Yes! Both are 5. (A% of B = B% of A)"},
    {"front": "Pause & Think: If 1/7 is 14.28%, what is 2/7?", "back": "Exactly double! 28.56%"},
    {"front": "Pause & Think: If price goes from 100 to 150, what is the % increase?", "back": "50% (Increase 50, Base 100: 50/100 * 100)"},
    {"front": "Pause & Think: If price goes from 150 to 100, what is the % decrease?", "back": "33.33% (Decrease 50, Base 150: 50/150 * 100)"},
    {"front": "Pause & Think: What does 100% mean in percentages?", "back": "The whole or complete unit (1)"}
]

conn = sqlite3.connect('study_station.db')
c = conn.cursor()
c.execute(
    "UPDATE book_chapter SET mind_map_data = ?, spaced_cards_hi = ?, spaced_cards_en = ? WHERE id = 4", 
    (mind_map, json.dumps(flashcards_hi, ensure_ascii=False), json.dumps(flashcards_en, ensure_ascii=False))
)
conn.commit()
conn.close()
print("Phase A assets (Mind Map & Flashcards) pushed successfully!")
