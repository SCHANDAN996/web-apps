import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
from models import db, JobAlert, SystemSettings

def get_setting(key):
    setting = SystemSettings.query.filter_by(setting_key=key).first()
    return setting.setting_value if setting else None

def trigger_auto_scrape(url):
    """
    Scrapes a URL, passes it to the configured AI model to extract job details,
    saves it to the database, and returns a status message.
    """
    if not url:
        return {"success": False, "message": "No URL provided."}

    # 1. Fetch AI Keys and Model
    api_keys_str = get_setting('gemini_api_keys') or get_setting('gemini_api_key')
    ai_model_name = get_setting('ai_model_name') or 'gemini-1.5-flash'
    
    if not api_keys_str:
        return {"success": False, "message": "Gemini API Keys are missing. Please configure them in Settings."}
        
    keys = [k.strip() for k in api_keys_str.split('\n') if k.strip()]
    if not keys:
        return {"success": False, "message": "No valid Gemini API Keys found."}

    # 2. Scrape the URL
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        text_content = soup.get_text(separator=' ', strip=True)
        text_content = text_content[:5000]
        
    except Exception as e:
        return {"success": False, "message": f"Failed to scrape URL: {str(e)}"}

    # 3. Call AI to extract details (with Multi-Key Fallback)
    ai_text = None
    last_error = None
    used_key = None
    
    for key in keys:
        try:
            genai.configure(api_key=key)
            model = genai.GenerativeModel(ai_model_name)
            
            prompt = f"""
            Extract job notification details from the following raw text scraped from a webpage.
            Format the output EXACTLY as a Python dictionary. DO NOT include any markdown formatting, backticks, or other text.
            Just a pure JSON-like string that can be evaluated using eval().
            
            Required keys:
            - "title": string
            - "organization": string
            - "post_name": string
            - "vacancies": string
            - "eligibility": string
            - "last_date": string
            - "category": string (one of GOVT, PRIVATE, BANKING)
            
            Raw Text:
            {text_content}
            """
            
            ai_response = model.generate_content(prompt)
            ai_text = ai_response.text.strip()
            used_key = key
            break # Success, exit the loop!
            
        except Exception as e:
            last_error = str(e)
            print(f"Key {key[:10]}... failed: {last_error}. Trying next...")
            continue
            
    if not ai_text:
        return {"success": False, "message": f"All API Keys failed! Last error: {last_error}"}

    # Parse and Save
    try:
        if ai_text.startswith("```"):
            ai_text = ai_text.strip("` \njsonpython")
            
        job_data = eval(ai_text)
        
        # 4. Save to Database
        new_job = JobAlert(
            title=job_data.get('title', 'Unknown Job Alert'),
            organization=job_data.get('organization', ''),
            post_name=job_data.get('post_name', ''),
            vacancies=job_data.get('vacancies', ''),
            eligibility=job_data.get('eligibility', ''),
            last_date=job_data.get('last_date', ''),
            application_url=url,
            category=job_data.get('category', 'GOVT')
        )
        db.session.add(new_job)
        db.session.commit()
        
        # 5. Trigger Telegram Notification
        from telegram_bot import send_telegram_alert
        telegram_status = send_telegram_alert(new_job)
        
        return {
            "success": True, 
            "message": f"Successfully added job using key ending in ...{used_key[-4:]}. Telegram status: {telegram_status}",
            "job": job_data
        }

    except Exception as e:
        return {"success": False, "message": f"AI Parsing or Database error: {str(e)}"}
