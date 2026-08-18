from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, current_app
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import io
import qrcode
from extensions import db
from models import Notice, Slider, Page, Document, Photo, Feedback, CareerApplication, AdmissionInquiry, OnlineAdmission, FeePayment, GlobalSettings

public_bp = Blueprint('public', __name__)

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf', 'doc', 'docx'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@public_bp.context_processor
def inject_global_settings():
    try:
        settings = GlobalSettings.query.first()
        return dict(settings=settings)
    except Exception as e:
        return dict(settings=None)

@public_bp.route('/')
def home():
    notices = Notice.query.order_by(Notice.date.desc()).limit(5).all()
    sliders = Slider.query.filter_by(active=True).order_by(Slider.display_order.asc(), Slider.id.desc()).all()
    return render_template('index.html', notices=notices, sliders=sliders)

def render_dynamic_page(template_name, slug):
    page = Page.query.filter_by(slug=slug).first()
    return render_template(template_name, page=page)

@public_bp.route('/about')
def about():
    return render_dynamic_page('about.html', 'about')

@public_bp.route('/cbse-info')
def cbse_info():
    docs = Document.query.filter_by(category='cbse_mandatory').order_by(Document.id.desc()).all()
    return render_template('cbse_info.html', documents=docs)

@public_bp.route('/gallery')
def gallery():
    photos = Photo.query.order_by(Photo.date.desc()).all()
    return render_template('gallery.html', photos=photos)

@public_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        message = request.form.get('message', '')
        feedback = Feedback(name=name, email=email, phone=phone, message=message)
        db.session.add(feedback)
        db.session.commit()
        flash('Thank you for getting in touch! Your message has been received.', 'success')
        return redirect(url_for('public.contact'))
    return render_template('contact.html')

@public_bp.route('/chairmans-desk')
def chairmans_desk():
    return render_dynamic_page('chairmans_desk.html', 'chairmans_desk')

@public_bp.route('/mds-desk')
def mds_desk():
    return render_dynamic_page('mds_desk.html', 'mds_desk')

@public_bp.route('/mission-vision')
def mission_vision():
    return render_dynamic_page('mission_vision.html', 'mission_vision')

@public_bp.route('/school-info')
def school_info():
    return render_dynamic_page('school_info.html', 'school_info')

@public_bp.route('/school-infrastructure')
def school_infrastructure():
    return render_dynamic_page('school_infrastructure.html', 'school_infrastructure')

@public_bp.route('/school-facilities')
def school_facilities():
    return render_dynamic_page('school_facilities.html', 'school_facilities')

@public_bp.route('/about-the-admission')
def about_the_admission():
    return render_dynamic_page('about_the_admission.html', 'about_the_admission')

@public_bp.route('/subject-offered')
def subject_offered():
    return render_dynamic_page('subject_offered.html', 'subject_offered')

@public_bp.route('/admission-form')
def admission_form():
    return render_template('admission_form.html')

@public_bp.route('/submit_admission', methods=['POST'])
def submit_admission():
    student_name = request.form.get('student_name')
    father_name = request.form.get('father_name')
    mother_name = request.form.get('mother_name')
    dob = request.form.get('dob')
    gender = request.form.get('gender')
    class_applied = request.form.get('class_applied')
    phone = request.form.get('phone')
    email = request.form.get('email', '')
    address = request.form.get('address')
    previous_school = request.form.get('previous_school', '')
    
    student_photo = request.files.get('student_photo')
    aadhar_card = request.files.get('aadhar_card')
    previous_marksheet = request.files.get('previous_marksheet')
    payment_receipt = request.files.get('payment_receipt')
    
    def save_file(file, folder):
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], folder)
            os.makedirs(upload_path, exist_ok=True)
            file.save(os.path.join(upload_path, unique_filename))
            return f"uploads/{folder}/{unique_filename}"
        return ""

    photo_path = save_file(student_photo, 'admissions')
    aadhar_path = save_file(aadhar_card, 'admissions')
    marksheet_path = save_file(previous_marksheet, 'admissions')
    receipt_path = save_file(payment_receipt, 'receipts')
    
    admission_fee_paid = bool(receipt_path)

    admission = OnlineAdmission(
        student_name=student_name, father_name=father_name, mother_name=mother_name,
        dob=dob, gender=gender, class_applied=class_applied, previous_school=previous_school,
        address=address, phone=phone, email=email, student_photo=photo_path,
        aadhar_card=aadhar_path, previous_marksheet=marksheet_path,
        admission_fee_paid=admission_fee_paid, payment_receipt=receipt_path
    )
    db.session.add(admission)
    db.session.commit()
    
    flash('Your admission application has been submitted successfully!', 'success')
    return redirect(url_for('public.home'))

@public_bp.route('/generate_qr')
def generate_qr():
    upi_id = request.args.get('upi_id', '')
    amount = request.args.get('amount', '0')
    
    if not upi_id:
        img = qrcode.make('Invalid UPI ID')
    else:
        upi_url = f"upi://pay?pa={upi_id}&pn=JS%20Public%20School&am={amount}&cu=INR"
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(upi_url)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
    
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@public_bp.route('/fee-payment', methods=['GET', 'POST'])
def fee_payment():
    if request.method == 'POST':
        student_name = request.form.get('student_name')
        admission_no = request.form.get('admission_no')
        class_name = request.form.get('class_name')
        amount_paid = request.form.get('amount_paid')
        receipt = request.files.get('payment_receipt')
        
        receipt_path = ""
        if receipt and receipt.filename and allowed_file(receipt.filename):
            filename = secure_filename(receipt.filename)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            unique_filename = f"{timestamp}_{filename}"
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'receipts')
            os.makedirs(upload_path, exist_ok=True)
            receipt.save(os.path.join(upload_path, unique_filename))
            receipt_path = f"uploads/receipts/{unique_filename}"
            
        if not receipt_path:
            flash('Payment receipt is required!', 'error')
            return redirect(url_for('public.fee_payment'))
            
        payment = FeePayment(
            student_name=student_name, admission_no=admission_no, 
            class_name=class_name, amount_paid=amount_paid, payment_receipt=receipt_path
        )
        db.session.add(payment)
        db.session.commit()
        
        flash('Fee payment receipt submitted successfully! Pending admin verification.', 'success')
        return redirect(url_for('public.home'))
        
    return render_template('fee_payment.html')

@public_bp.route('/prospectus')
def prospectus():
    doc = Document.query.filter_by(category='prospectus').order_by(Document.id.desc()).first()
    return render_template('prospectus.html', document=doc)

@public_bp.route('/advertisment')
def advertisment():
    return render_template('advertisment.html')

@public_bp.route('/tc-downloads')
def tc_downloads():
    docs = Document.query.filter_by(category='tc_download').order_by(Document.id.desc()).all()
    return render_template('tc_downloads.html', documents=docs)

@public_bp.route('/other-downloads')
def other_downloads():
    docs = Document.query.filter_by(category='general').order_by(Document.id.desc()).all()
    return render_template('other_downloads.html', documents=docs)

@public_bp.route('/feedback')
def feedback():
    return render_template('feedback.html')

@public_bp.route('/news')
def news():
    notices = Notice.query.order_by(Notice.date.desc()).all()
    return render_template('news.html', notices=notices)

@public_bp.route('/career')
def career():
    return render_template('career.html')

@public_bp.route('/career_submit', methods=['POST'])
def career_submit():
    name = request.form['name']
    email = request.form['email']
    phone = request.form['phone']
    position = request.form['position']
    resume_link = request.form['resume_link']
    
    career_app = CareerApplication(name=name, email=email, phone=phone, position=position, resume_link=resume_link)
    db.session.add(career_app)
    db.session.commit()
    flash('Your application has been submitted successfully!', 'success')
    return redirect(url_for('public.career'))

@public_bp.route('/admission', methods=('GET', 'POST'))
def admission():
    if request.method == 'POST':
        student_name = request.form['student_name']
        parent_name = request.form['parent_name']
        phone = request.form['phone']
        class_applied = request.form['class_applied']
        
        if not student_name or not phone:
            flash('Name and Phone are required!', 'error')
        else:
            inquiry = AdmissionInquiry(student_name=student_name, parent_name=parent_name, phone=phone, class_applied=class_applied)
            db.session.add(inquiry)
            db.session.commit()
            flash('Admission inquiry submitted successfully! We will contact you soon.', 'success')
            return redirect(url_for('public.admission'))
            
    return render_template('admission.html')
