import os

# 1. Update contact.html
contact_path = r"c:\Users\Admin\Desktop\js public\flask_jspschandauli\templates\contact.html"
with open(contact_path, 'r', encoding='utf-8') as f:
    contact_code = f.read()

# Replace <form action="#" method="POST">
contact_code = contact_code.replace('<form class="customform" action="#" method="POST">', '<form class="customform" action="{{ url_for(\'contact\') }}" method="POST">')
# Replace mobile input
contact_code = contact_code.replace('name="mobile"', 'name="phone"')
# Delete subject input
import re
contact_code = re.sub(r'<div class="s-12">\s*<input name="subject"[^>]+>\s*</div>', '', contact_code)
# Replace button type
contact_code = contact_code.replace('type="button">Submit</button>', 'type="submit">Submit Message</button>')

with open(contact_path, 'w', encoding='utf-8') as f:
    f.write(contact_code)

# 2. Update base.html
base_path = r"c:\Users\Admin\Desktop\js public\flask_jspschandauli\templates\base.html"
with open(base_path, 'r', encoding='utf-8') as f:
    base_code = f.read()

# Change subject input to phone
old_subject_input = '''<input name="subject" class="subject border-radius" placeholder="Subject"
                                            title="Subject" type="text" required />'''
new_phone_input = '''<input name="phone" class="border-radius" placeholder="Your Phone Number"
                                            title="Phone" type="text" required />'''
base_code = base_code.replace(old_subject_input, new_phone_input)

with open(base_path, 'w', encoding='utf-8') as f:
    f.write(base_code)

print("Contact forms successfully connected to backend.")
