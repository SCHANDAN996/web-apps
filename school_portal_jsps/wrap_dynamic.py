import os

directory = 'templates'
os.chdir(directory)

pages = [
    'about.html', 'chairmans_desk.html', 'mds_desk.html', 
    'mission_vision.html', 'school_info.html', 'school_infrastructure.html',
    'school_facilities.html', 'about_the_admission.html', 'subject_offered.html'
]

for filename in pages:
    if not os.path.exists(filename):
        continue
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()

    # Prevent double wrapping
    if '{% if page and page.content %}' in content:
        print(f"Skipping {filename}, already wrapped.")
        continue

    # We want to wrap everything inside {% block content %} and {% endblock %}
    start_tag = '{% block content %}'
    end_tag = '{% endblock %}'
    
    start_idx = content.find(start_tag)
    end_idx = content.rfind(end_tag)

    if start_idx != -1 and end_idx != -1:
        start_idx += len(start_tag)
        inner_html = content[start_idx:end_idx]
        
        wrapped_html = f"""
{{% if page and page.content %}}
<div class="section background-white">
    <div class="line">
        <div class="margin">
             {{{{ page.content | safe }}}}
        </div>
    </div>
</div>
{{% else %}}
{inner_html}
{{% endif %}}
"""
        new_content = content[:start_idx] + wrapped_html + content[end_idx:]
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully wrapped {filename}")
    else:
        print(f"Could not find block content in {filename}")

print("Done wrapping templates.")
