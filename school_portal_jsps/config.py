import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'jsps_chandauli_secure_key_fallback'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'school.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images', 'gallery')
    SLIDERS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'images', 'sliders')
    DOCUMENTS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'documents')
    ASSIGNMENTS_FOLDER = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'static', 'assignments')
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME') or 'admin'
    ADMIN_PASSWORD_HASH = os.environ.get('ADMIN_PASSWORD_HASH') or 'scrypt:32768:8:1$Y3pBkqA2nXZ9uP0z$0d86c8d207865db2dbf2d2bbbe3f7b2c019d1bb8fb77953288921e42a0445d3e09880f745ed4b04d1f2e8f17bc16f6b5fbc40d5885c30b91d2d09ef1b4ebcba5' # Default password is jsps@admin123
    JWT_EXPIRY_HOURS = int(os.environ.get('JWT_EXPIRY_HOURS', '168'))
    
    # Session Security
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    # SESSION_COOKIE_SECURE = True # Uncomment in production with HTTPS
