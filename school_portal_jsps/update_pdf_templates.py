import os, re

dir_path = r"c:\Users\Admin\Desktop\js public\flask_jspschandauli\templates"

# 1. Update single-document iframe pages
single_pages = ['admission_form.html', 'prospectus.html']
for page in single_pages:
    path = os.path.join(dir_path, page)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Replace the hardcoded iframe string using regex
        iframe_pattern = r'<iframe[^>]*src="\{\{\s*url_for\([^)]+\)\s*\}\}"[^>]*></iframe>'
        replacement = '''
{% if document %}
<iframe height="800" src="{{ url_for('static', filename=document.file_path) }}" type="application/pdf" width="100%"></iframe>
{% else %}
<div class="alert alert-warning text-center padding"><i class="icon-sli-doc margin-right-10"></i> No PDF uploaded yet. Please check back later or contact administration.</div>
{% endif %}'''
        new_content = re.sub(iframe_pattern, replacement.strip(), content)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

# 2. Update multi-document list pages
list_pages = ['cbse_info.html', 'tc_downloads.html', 'other_downloads.html']
list_replacement = r'''<ul class="margin-bottom-0">
    {% if documents %}
        {% for doc in documents %}
        <li class="margin-bottom-10">
            <a class="button border-radius background-dark text-white padding" href="{{ url_for('static', filename=doc.file_path) }}" target="_blank" style="display:block;">
                <i class="icon-sli-doc margin-right-10"></i> {{ doc.title|upper }}
            </a>
        </li>
        {% endfor %}
    {% else %}
        <li class="margin-bottom-10"><p>No documents uploaded in this category yet.</p></li>
    {% endif %}
</ul>'''

for page in list_pages:
    path = os.path.join(dir_path, page)
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Gut the <ul>...</ul> block
        ul_pattern = r'<ul class="margin-bottom-0">.*?</ul>'
        new_content = re.sub(ul_pattern, list_replacement, content, flags=re.DOTALL)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)

print("Templates successfully updated to dynamic CMS Jinja tags.")
