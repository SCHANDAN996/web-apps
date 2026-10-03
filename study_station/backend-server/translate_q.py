import sqlite3
import json
import urllib.request
import urllib.parse
import time

def translate(text, target="en", source="hi"):
    if not text: return text
    try:
        url = "https://translate.googleapis.com/translate_a/single?client=gtx&sl={}&tl={}&dt=t&q={}".format(source, target, urllib.parse.quote(text))
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        return "".join([x[0] for x in result[0]])
    except Exception as e:
        print(f"Translate Error: {e}")
        return text

def main():
    conn = sqlite3.connect('study_station.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, practice_questions_hi FROM book_chapter WHERE practice_questions_hi IS NOT NULL AND practice_questions_en IS NULL")
    rows = cursor.fetchall()

    for row in rows:
        ch_id = row[0]
        hi_qs = json.loads(row[1])[:10]  # Only translate first 10 for demonstration
        en_qs = []
        
        print(f"Translating {len(hi_qs)} questions for chapter {ch_id}...")
        for i, q in enumerate(hi_qs):
            print(f"Translating Q{i+1}/{len(hi_qs)}...")
            en_q = {
                "id": q.get("id"),
                "question": translate(q.get("question")),
                "options": [translate(opt) for opt in q.get("options", [])],
                "answer": q.get("answer"),
                "solution": translate(q.get("solution")),
                "section": translate(q.get("section"))
            }
            # Special case for KaTeX (translation sometimes messes up $)
            en_q["question"] = en_q["question"].replace("$ ", "$").replace(" $", "$").replace("\\ ", "\\")
            en_qs.append(en_q)
            time.sleep(0.5) # respect rate limits roughly
            
        cursor.execute("UPDATE book_chapter SET practice_questions_en = ? WHERE id = ?", (json.dumps(en_qs, ensure_ascii=False), ch_id))
        conn.commit()
        print(f"Chapter {ch_id} translation complete!")

if __name__ == '__main__':
    main()
