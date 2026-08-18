from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps
from datetime import datetime
from extensions import db
from models import Notice, Slider, Page, Document, Photo, CareerApplication, AdmissionInquiry, OnlineAdmission, FeePayment, GlobalSettings, StudentProfile, TeacherProfile, LeaveApplication, ParentMessage, FeeInvoice

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('admin.login'))
        if session.get('role') not in ('admin', 'staff_admin', 'staff'):
            flash('You do not have permission to access this page.', 'error')
            return redirect(url_for('public.home'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == current_app.config['ADMIN_USERNAME'] and check_password_hash(current_app.config['ADMIN_PASSWORD_HASH'], password):
            session['logged_in'] = True
            session['role'] = 'admin'
            session['user_id'] = 0
            flash('Logged in successfully!', 'success')
            return redirect(url_for('admin.admin_dashboard'))
        else:
            flash('Invalid username or password', 'error')
            
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('public.home'))

@admin_bp.route('/')
@login_required
def admin_dashboard():
    admissions_count = AdmissionInquiry.query.count()
    notices_count = Notice.query.count()
    careers_count = CareerApplication.query.count()
    students_count = StudentProfile.query.count()
    teachers_count = TeacherProfile.query.count()
    pending_leave_count = LeaveApplication.query.filter_by(status='Pending').count()
    open_messages_count = ParentMessage.query.filter_by(status='Open').count()
    pending_fee_count = FeeInvoice.query.filter(FeeInvoice.status.in_(['Pending', 'Partial', 'Overdue'])).count()
    return render_template('admin/dashboard.html', 
                          admissions_count=admissions_count, 
                          notices_count=notices_count, 
                          careers_count=careers_count,
                          students_count=students_count,
                          teachers_count=teachers_count,
                          pending_leave_count=pending_leave_count,
                          open_messages_count=open_messages_count,
                          pending_fee_count=pending_fee_count)

@admin_bp.route('/admissions')
@login_required
def admin_admissions():
    admissions = AdmissionInquiry.query.order_by(AdmissionInquiry.date.desc()).all()
    return render_template('admin/admissions.html', admissions=admissions)

@admin_bp.route('/careers')
@login_required
def admin_careers():
    careers = CareerApplication.query.order_by(CareerApplication.date.desc()).all()
    return render_template('admin/careers.html', careers=careers)

@admin_bp.route('/online_admissions')
@login_required
def admin_online_admissions():
    admissions = OnlineAdmission.query.order_by(OnlineAdmission.application_date.desc()).all()
    return render_template('admin/online_admissions.html', admissions=admissions)

@admin_bp.route('/online_admissions/approve/<int:admission_id>', methods=['POST'])
@login_required
def approve_online_admission(admission_id):
    admission = OnlineAdmission.query.get_or_404(admission_id)
    admission.application_status = "Approved"
    db.session.commit()
    flash('Admissions application approved successfully!', 'success')
    return redirect(url_for('admin.admin_online_admissions'))

@admin_bp.route('/online_admissions/reject/<int:admission_id>', methods=['POST'])
@login_required
def reject_online_admission(admission_id):
    admission = OnlineAdmission.query.get_or_404(admission_id)
    admission.application_status = "Rejected"
    db.session.commit()
    flash('Admissions application rejected.', 'success')
    return redirect(url_for('admin.admin_online_admissions'))

@admin_bp.route('/fee_records')
@login_required
def admin_fee_records():
    fees = FeePayment.query.order_by(FeePayment.payment_date.desc()).all()
    return render_template('admin/fee_records.html', fees=fees)

@admin_bp.route('/fee_records/approve/<int:fee_id>', methods=['POST'])
@login_required
def approve_fee(fee_id):
    fee = FeePayment.query.get_or_404(fee_id)
    fee.payment_status = "Approved"
    db.session.commit()
    flash('Fee payment approved successfully!', 'success')
    return redirect(url_for('admin.admin_fee_records'))

@admin_bp.route('/fee_records/reject/<int:fee_id>', methods=['POST'])
@login_required
def reject_fee(fee_id):
    fee = FeePayment.query.get_or_404(fee_id)
    fee.payment_status = "Rejected"
    db.session.commit()
    flash('Fee payment rejected.', 'success')
    return redirect(url_for('admin.admin_fee_records'))

@admin_bp.route('/notices')
@login_required
def admin_notices():
    notices = Notice.query.order_by(Notice.date.desc()).all()
    return render_template('admin/notices.html', notices=notices)

@admin_bp.route('/notices/add', methods=['POST'])
@login_required
def add_notice():
    title = request.form.get('title', '').strip()
    content = request.form.get('content', '').strip()
    if not title:
        flash('Notice title is required.', 'error')
        return redirect(url_for('admin.admin_notices'))
    notice = Notice(title=title, content=content)
    db.session.add(notice)
    db.session.commit()
    flash('Notice published successfully.', 'success')
    return redirect(url_for('admin.admin_notices'))

@admin_bp.route('/notices/delete/<int:notice_id>', methods=['POST'])
@login_required
def delete_notice(notice_id):
    notice = Notice.query.get_or_404(notice_id)
    db.session.delete(notice)
    db.session.commit()
    flash('Notice deleted successfully!', 'success')
    return redirect(url_for('admin.admin_notices'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    settings = GlobalSettings.query.first()
    if not settings:
        settings = GlobalSettings()
        db.session.add(settings)
        db.session.commit()

    if request.method == 'POST':
        settings.phone1 = request.form.get('phone1', '')
        settings.phone2 = request.form.get('phone2', '')
        settings.email = request.form.get('email', '')
        settings.address = request.form.get('address', '')
        settings.motto = request.form.get('motto', '')
        settings.marquee_text = request.form.get('marquee_text', '')
        settings.facebook = request.form.get('facebook', '')
        settings.twitter = request.form.get('twitter', '')
        settings.instagram = request.form.get('instagram', '')
        settings.youtube = request.form.get('youtube', '')
        settings.payment_upi_id = request.form.get('payment_upi_id', '')
        try:
            settings.admission_fee = int(request.form.get('admission_fee', 0))
        except ValueError:
            settings.admission_fee = 0

        db.session.commit()
        flash('Global settings updated successfully!', 'success')
        return redirect(url_for('admin.admin_settings'))

    return render_template('admin/settings.html', settings=settings)

@admin_bp.route('/gallery')
@login_required
def admin_gallery():
    photos = Photo.query.order_by(Photo.id.desc()).all()
    return render_template('admin/admin_gallery.html', photos=photos)

@admin_bp.route('/gallery/upload', methods=['POST'])
@login_required
def upload_photo():
    file = request.files.get('photo')
    category = request.form.get('category', 'All')
    if not file or file.filename == '':
        flash('Please select a photo to upload.', 'error')
        return redirect(url_for('admin.admin_gallery'))
    if not allowed_file(file.filename):
        flash('Unsupported file format.', 'error')
        return redirect(url_for('admin.admin_gallery'))

    filename = secure_filename(file.filename)
    stamped = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], stamped)
    file.save(file_path)
    db.session.add(Photo(filename=stamped, category=category))
    db.session.commit()
    flash('Photo uploaded successfully.', 'success')
    return redirect(url_for('admin.admin_gallery'))

@admin_bp.route('/gallery/delete/<int:photo_id>', methods=['POST'])
@login_required
def delete_photo(photo_id):
    photo = Photo.query.get_or_404(photo_id)
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], photo.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(photo)
    db.session.commit()
    flash('Photo deleted successfully!', 'success')
    return redirect(url_for('admin.admin_gallery'))

@admin_bp.route('/pages', methods=['GET', 'POST'])
@login_required
def admin_pages():
    if request.method == 'POST':
        slug = request.form.get('page_slug')
        content = request.form.get('content')
        
        banner_path = None
        if 'banner_image' in request.files:
            file = request.files['banner_image']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                banners_dir = os.path.join(current_app.root_path, 'static', 'images', 'banners')
                os.makedirs(banners_dir, exist_ok=True)
                file_path = os.path.join(banners_dir, filename)
                file.save(file_path)
                banner_path = f'images/banners/{filename}'

        if slug and content is not None:
            page = Page.query.filter_by(slug=slug).first()
            if page:
                page.content = content
                if banner_path:
                    page.banner_image = banner_path
                db.session.commit()
                flash('Page content updated successfully!', 'success')
            else:
                flash('Page not found.', 'error')
        else:
            flash('Failed to update page content.', 'error')
        return redirect(url_for('admin.admin_pages') + '?page=' + (slug or ''))

    selected_slug = request.args.get('page')
    pages_list = Page.query.order_by(Page.id).all()
    
    selected_page_data = None
    if selected_slug:
        selected_page_data = Page.query.filter_by(slug=selected_slug).first()
    elif pages_list:
        selected_page_data = pages_list[0]

    return render_template('admin/pages.html', pages=pages_list, selected_page=selected_page_data)

@admin_bp.route('/sliders', methods=['GET', 'POST'])
@login_required
def admin_sliders():
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['image']
        title = request.form.get('title', '')
        subtitle = request.form.get('subtitle', '')
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['SLIDERS_FOLDER'], filename)
            file.save(file_path)
            
            db_path = f'images/sliders/{filename}'
            
            slider = Slider(image_path=db_path, title=title, subtitle=subtitle)
            db.session.add(slider)
            db.session.commit()
            flash('Slider added successfully!', 'success')
            return redirect(url_for('admin.admin_sliders'))
    
    sliders = Slider.query.order_by(Slider.display_order.asc(), Slider.id.desc()).all()
    return render_template('admin/sliders.html', sliders=sliders)

@admin_bp.route('/sliders/delete/<int:slider_id>', methods=['POST'])
@login_required
def delete_slider(slider_id):
    slider = Slider.query.get_or_404(slider_id)
    file_path = os.path.join(current_app.config['SLIDERS_FOLDER'], os.path.basename(slider.image_path))
    if os.path.exists(file_path):
        os.remove(file_path)
        
    db.session.delete(slider)
    db.session.commit()
    flash('Slider deleted successfully!', 'success')
    return redirect(url_for('admin.admin_sliders'))

@admin_bp.route('/sliders/update/<int:slider_id>', methods=['POST'])
@login_required
def update_slider(slider_id):
    slider = Slider.query.get_or_404(slider_id)
    slider.display_order = request.form.get('display_order', 0, type=int)
    slider.active = 'active' in request.form
    
    db.session.commit()
    flash('Slider updated successfully!', 'success')
    return redirect(url_for('admin.admin_sliders'))

@admin_bp.route('/documents', methods=['GET', 'POST'])
@login_required
def admin_documents():
    if request.method == 'POST':
        if 'document' not in request.files:
            flash('No file part', 'error')
            return redirect(request.url)
        
        file = request.files['document']
        title = request.form.get('title', '')
        category = request.form.get('category', 'general')
        
        if file.filename == '':
            flash('No selected file', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(current_app.config['DOCUMENTS_FOLDER'], filename)
            file.save(file_path)
            
            db_path = f'documents/{filename}'
            
            doc = Document(title=title, category=category, file_path=db_path)
            db.session.add(doc)
            db.session.commit()
            flash('Document uploaded successfully!', 'success')
            return redirect(url_for('admin.admin_documents'))
    
    docs = Document.query.order_by(Document.id.desc()).all()
    return render_template('admin/documents.html', documents=docs)

@admin_bp.route('/documents/delete/<int:doc_id>', methods=['POST'])
@login_required
def delete_document(doc_id):
    doc = Document.query.get_or_404(doc_id)
    file_path = os.path.join(current_app.config['DOCUMENTS_FOLDER'], os.path.basename(doc.file_path))
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(doc)
    db.session.commit()
    flash('Document deleted successfully!', 'success')
    return redirect(url_for('admin.admin_documents'))
