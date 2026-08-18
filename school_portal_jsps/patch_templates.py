import os
import re

templates_dir = os.path.join(os.path.dirname(__file__), 'templates')

def patch_templates():
    public_routes = ['home', 'about', 'cbse_info', 'gallery', 'contact', 'chairmans_desk', 'mds_desk', 'mission_vision', 'school_info', 'school_infrastructure', 'school_facilities', 'about_the_admission', 'subject_offered', 'admission_form', 'submit_admission', 'generate_qr', 'fee_payment', 'prospectus', 'advertisment', 'tc_downloads', 'other_downloads', 'feedback', 'news', 'career', 'career_submit', 'admission']
    
    admin_routes = ['login', 'logout', 'admin_dashboard', 'admin_admissions', 'admin_careers', 'admin_online_admissions', 'approve_online_admission', 'reject_online_admission', 'admin_fee_records', 'approve_fee', 'reject_fee', 'admin_notices', 'delete_notice', 'admin_settings', 'admin_gallery', 'delete_photo', 'admin_pages', 'admin_sliders', 'delete_slider', 'update_slider', 'admin_documents', 'delete_document']

    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace url_for('route')
                for route in public_routes:
                    content = re.sub(rf"url_for\(['\"]{route}['\"]\)", f"url_for('public.{route}')", content)
                for route in admin_routes:
                    content = re.sub(rf"url_for\(['\"]{route}['\"]\)", f"url_for('admin.{route}')", content)
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)

if __name__ == '__main__':
    patch_templates()
    print("Templates patched.")
