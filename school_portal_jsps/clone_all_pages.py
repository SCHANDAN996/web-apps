import os
import requests
from bs4 import BeautifulSoup
import re

BASE_URL = "https://jspschandauli.com/"

PAGES = [
    "prospectus.html",
    "advertisment.html",
    "tc-downloads.html",
    "other-downloads.html",
    "feedback.html",
    "gallery.html"
]

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")

def log(msg):
    with open("scrape_log.txt", "a", encoding="utf-8") as f:
        f.write(msg + "\n")

def convert_to_jinja(html_content):
    # Convert src="img/..." to src="{{ url_for('static', filename='img/...') }}"
    html_content = re.sub(r'src="(img/[^"]+)"', r'src="{{ url_for(\'static\', filename=\'\1\') }}"', html_content)
    # Convert href="css/..."
    html_content = re.sub(r'href="(css/[^"]+)"', r'href="{{ url_for(\'static\', filename=\'\1\') }}"', html_content)
    # Convert href="js/..."
    html_content = re.sub(r'href="(js/[^"]+)"', r'href="{{ url_for(\'static\', filename=\'\1\') }}"', html_content)
    # Correct forms (Optional: leave action as empty or "#" for now, or point to actual routes if possible)
    return html_content

for page in PAGES:
    log(f"Fetching {page}...")
    try:
        response = requests.get(BASE_URL + page, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content
            main_content = soup.find('main', role='main')
            if not main_content:
                main_content = soup.find('article')
                
            if main_content:
                # Get the inner HTML of main
                inner_html = ""
                for child in main_content.children:
                    inner_html += str(child)
                
                inner_html = convert_to_jinja(inner_html)
                
                # Create the template content
                template_name = page.replace("-", "_")
                
                # Title
                title_tag = soup.find('title')
                title = title_tag.text if title_tag else "JS Public School"
                
                flask_template = f"{{% extends 'base.html' %}}\n{{% block title %}}{title}{{% endblock %}}\n\n{{% block content %}}\n{inner_html}\n{{% endblock %}}"
                
                file_path = os.path.join(TEMPLATE_DIR, template_name)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(flask_template)
                log(f"Successfully created {template_name}")
            else:
                log(f"Main content not found on {page}")
        else:
            log(f"Failed to fetch {page}: Status code {response.status_code}")
    except Exception as e:
        log(f"Error fetching {page}: {e}")
