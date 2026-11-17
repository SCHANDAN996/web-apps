"""Bounded Hindi-only model pilot; never edits books or prints credentials."""
import json, os, time, urllib.request, urllib.error, re
from pathlib import Path
MODELS = ["nvidia/nemotron-3-ultra-550b-a55b", "deepseek-ai/deepseek-v4.1-flash"]
GOLD = ["b","c","a","d","b","a","c","d","b","a"]
QUIZ = """1. स्वर कौन है? (a) क (b) आ (c) त (d) म
2. सर्वनाम कौन है? (a) सुंदर (b) दौड़ना (c) वह (d) पुस्तक
3. संज्ञा कौन है? (a) पुस्तक (b) धीरे (c) और (d) लेकिन
4. विशेषण कौन है? (a) राम (b) वह (c) दौड़ना (d) सुंदर
5. क्रिया कौन है? (a) लाल (b) दौड़ना (c) नदी (d) मैं
6. 'दिन' का विलोम? (a) रात (b) सुबह (c) समय (d) प्रकाश
7. 'जल' का पर्याय? (a) अग्नि (b) आकाश (c) पानी (d) हवा
8. शुद्ध वर्तनी? (a) विधालय (b) विदयालय (c) विद्यालयय (d) विद्यालय
9. 'लड़का' का स्त्रीलिंग? (a) लड़के (b) लड़की (c) लड़कों (d) लड़कपन
10. 'लड़का' का प्रत्यक्ष बहुवचन? (a) लड़के (b) लड़कों (c) लड़कियाँ (d) लड़कपन"""
PROMPT = """आप हिंदी परीक्षा की पुस्तक के लेखक हैं। सीधे हिंदी में सोचकर लिखें; अंग्रेज़ी मसौदा या अनुवाद नहीं।
केवल वैध JSON लौटाएँ, कोई markdown fence नहीं।
ढाँचा: {"lesson":"...","answers":["a",...],"questions":[{"n":1,"question":"...","options":{"a":"...","b":"...","c":"...","d":"..."},"answer":"a","explanation":"..."}]}
lesson: कक्षा 10 स्तर के पाठक के लिए 'वर्ण और वर्तनी' पर 250-350 हिंदी शब्दों का सहज पाठ, सही उदाहरण और एक स्मरण प्रश्न।
answers: नीचे दिए 10 परीक्षण प्रश्नों के उत्तर उसी क्रम में, केवल a/b/c/d।
questions: वर्ण-वर्तनी पर ठीक 25 नए, आपस में अलग अभ्यास प्रश्न; हर प्रश्न में चार अलग विकल्प, एक सही उत्तर और 1-2 वाक्यों का हिंदी समाधान। वर्तनी के गलत विकल्प जानबूझकर गलत ही रखें। गढ़ा PYQ, स्रोत, आँकड़ा या संदिग्ध वर्ण-गिनती न दें।
परीक्षण प्रश्न:
""" + QUIZ
out = Path("pilot-results"); out.mkdir(exist_ok=True)
key = next((os.environ.get(n,"").strip() for n in ("NVIDIA_API_KEY_3","NVIDIA_API_KEY_4") if os.environ.get(n,"").strip()), "")
if not key:
    raise SystemExit("Missing active NVIDIA key (3 or 4); no requests made")
summaries = []
try:
    req = urllib.request.Request("https://integrate.api.nvidia.com/v1/models", headers={"Authorization":"Bearer "+key})
    with urllib.request.urlopen(req,timeout=40) as response: catalog=json.load(response)
    available=[x["id"] for x in catalog.get("data",[]) if "deepseek" in x.get("id","").lower()]
    print("AVAILABLE_DEEPSEEK_MODELS: "+json.dumps(available),flush=True)
    preferred=["deepseek-ai/deepseek-v3.2","deepseek-ai/deepseek-v3.1","deepseek-ai/deepseek-v3","deepseek-ai/deepseek-r1"]
    candidates=[m for m in preferred if m in available]
    candidates += [m for m in available if m not in candidates and m != "deepseek-ai/deepseek-v4.1-flash"]
    MODELS=candidates[:1]
    if not MODELS: print("NO_ALTERNATIVE_DEEPSEEK_MODEL_IN_AUTHENTICATED_CATALOG",flush=True)
except Exception as e:
    print("CATALOG_ERROR: "+type(e).__name__,flush=True)
    MODELS=[]

for index, model in enumerate(MODELS):
    if index: time.sleep(20)
    started = time.monotonic()
    summary = {"model":model,"prompt_identical":True,"attempts":1}
    try:
        body = {"model":model,"messages":[{"role":"system","content":"आप हिंदी व्याकरण के लेखक हैं। केवल माँगा हुआ JSON दें।"},{"role":"user","content":PROMPT}],"temperature":0.2,"max_tokens":7000,"stream":False}
        req = urllib.request.Request("https://integrate.api.nvidia.com/v1/chat/completions", data=json.dumps(body,ensure_ascii=False).encode(), headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"})
        with urllib.request.urlopen(req,timeout=240) as response: result=json.load(response)
        choice=result["choices"][0]; content=choice["message"].get("content") or ""
        (out / (str(index)+".txt")).write_text(content,encoding="utf-8")
        summary.update(seconds=round(time.monotonic()-started,2),finish_reason=choice.get("finish_reason"),usage=result.get("usage",{}))
        cleaned=re.sub(r"^\s*```(?:json)?\s*|\s*```\s*$","",content.strip())
        data=json.loads(cleaned)
        answers=data.get("answers",[])
        qs=data.get("questions",[])
        summary.update(json_valid=True,quiz_correct=sum(a==b for a,b in zip(answers,GOLD)),quiz_answer_count=len(answers),question_count=len(qs),lesson_words=len(data.get("lesson","").split()))
        summary["format_valid_count"]=sum(isinstance(q,dict) and q.get("n")==i and isinstance(q.get("options"),dict) and set(q["options"])==set("abcd") and len(set(q["options"].values()))==4 and q.get("answer") in "abcd" and bool(q.get("explanation")) for i,q in enumerate(qs,1))
        summary["unique_question_count"]=len({q.get("question","").strip() for q in qs})
    except urllib.error.HTTPError as e:
        summary.update(error="HTTP "+str(e.code),seconds=round(time.monotonic()-started,2))
    except Exception as e:
        summary.update(error=type(e).__name__,seconds=round(time.monotonic()-started,2))
    summaries.append(summary)
    print(json.dumps(summary,ensure_ascii=False),flush=True)
(out/"summary.json").write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding="utf-8")
print("PILOT_FINISHED: raw answers require human content review; no production changes.")
