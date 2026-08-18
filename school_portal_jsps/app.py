from flask import Flask
from config import Config
from extensions import db
from models import GlobalSettings, Page
from flask_wtf.csrf import CSRFProtect
import os

csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf.init_app(app)

    # Ensure upload folders exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['SLIDERS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['DOCUMENTS_FOLDER'], exist_ok=True)
    os.makedirs(app.config['ASSIGNMENTS_FOLDER'], exist_ok=True)
    
    # Ad-hoc receipts and admissions folders inside UPLOAD_FOLDER
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'receipts'), exist_ok=True)
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'admissions'), exist_ok=True)

    with app.app_context():
        # This will create tables if they don't exist based on SQLAlchemy models
        db.create_all()
        
        # Seed default global settings if empty
        if not GlobalSettings.query.first():
            settings = GlobalSettings(
                phone1='08125043333', 
                phone2='08127063333', 
                email='jspublicschool9@gmail.com', 
                address='Village Kasimpur-Pandeypur, Mughalsarai- Chakia Road, Chandauli', 
                motto='Practice patience perseverance.', 
                marquee_text='Welcome to J S Public School, best school in Chandauli!', 
                facebook='#', twitter='#', instagram='#', youtube='#', 
                admission_fee=500, payment_upi_id='admin@okbank'
            )
            db.session.add(settings)
            db.session.commit()

        # Seed default pages if empty
        if not Page.query.first():
            default_pages = [
                ('about', 'About Us'),
                ('chairmans_desk', "Chairman's Desk"),
                ('mds_desk', "M.D's Desk"),
                ('mission_vision', 'Vision & Mission'),
                ('school_info', 'School Info'),
                ('school_infrastructure', 'School Infrastructure'),
                ('school_facilities', 'School Facilities'),
                ('about_the_admission', 'About the Admission'),
                ('subject_offered', 'Subject Offered')
            ]
            for slug, title in default_pages:
                page = Page(slug=slug, title=title, content='')
                db.session.add(page)
            db.session.commit()

    from routes.public import public_bp
    from routes.admin import admin_bp
    from routes.auth import auth_bp
    from routes.admin_automation import admin_auto_bp
    from routes.student import student_bp
    from routes.parent import parent_bp
    from routes.api import api_bp
    from routes.admin_erp import admin_erp_bp
    from routes.teacher import teacher_bp
    from routes.staff import staff_bp
    from routes.driver import driver_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_auto_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(parent_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_erp_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(staff_bp)
    app.register_blueprint(driver_bp)
    csrf.exempt(api_bp)

    with app.app_context():
        from seed_demo_users import seed_demo_users
        seed_demo_users()

    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
