import os
import re

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

def patch_csrf():
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if it has a form with POST method and doesn't already have csrf_token
                if re.search(r'<form[^>]*method=[\'"]POST[\'"][^>]*>', content, re.IGNORECASE) and 'csrf_token' not in content:
                    # Find all form tags and append the hidden input inside
                    content = re.sub(
                        r'(<form[^>]*method=[\'"]POST[\'"][^>]*>)',
                        r'\1\n                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>',
                        content,
                        flags=re.IGNORECASE
                    )
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

if __name__ == '__main__':
    patch_csrf()
    print("CSRF tokens injected.")
