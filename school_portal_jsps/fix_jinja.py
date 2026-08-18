import os
import glob

directory = 'templates'
os.chdir(directory)

for filename in glob.glob('*.html'):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Replacing escaped quotes
    if "url_for(\\'static\\'" in content or r"url_for(\'static\'" in content:
        content = content.replace(r"url_for(\'static\'", 'url_for("static"')
        content = content.replace(r"url_for(\\'static\\'", 'url_for("static"')
        content = content.replace(r"filename=\'", 'filename="')
        content = content.replace(r"filename=\\'", 'filename="')
        content = content.replace(r"\')", '")')
        content = content.replace(r"\\')", '")')
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed {filename}")
print("Done fixing syntax.")
