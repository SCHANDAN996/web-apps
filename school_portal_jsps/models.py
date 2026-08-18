from datetime import datetime
from extensions import db

class Notice(db.Model):
    __tablename__ = 'notices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class AdmissionInquiry(db.Model):
    __tablename__ = 'admissions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_name = db.Column(db.String(255), nullable=False)
    parent_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    class_applied = db.Column(db.String(50), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class Photo(db.Model):
    __tablename__ = 'photos'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), default='All')
    date = db.Column(db.DateTime, default=datetime.utcnow)

class CareerApplication(db.Model):
    __tablename__ = 'careers'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    resume_link = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class GlobalSettings(db.Model):
    __tablename__ = 'global_settings'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    phone1 = db.Column(db.String(20))
    phone2 = db.Column(db.String(20))
    email = db.Column(db.String(255))
    address = db.Column(db.Text)
    motto = db.Column(db.Text)
    marquee_text = db.Column(db.Text)
    facebook = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    youtube = db.Column(db.String(255))
    admission_fee = db.Column(db.Integer, default=0)
    payment_upi_id = db.Column(db.String(255))

class Page(db.Model):
    __tablename__ = 'pages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text)
    banner_image = db.Column(db.String(255))

class Slider(db.Model):
    __tablename__ = 'sliders'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    image_path = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(255))
    subtitle = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    display_order = db.Column(db.Integer, default=0)

class Document(db.Model):
    __tablename__ = 'documents'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255), nullable=False)

class Feedback(db.Model):
    __tablename__ = 'feedbacks'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    message = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)

class OnlineAdmission(db.Model):
    __tablename__ = 'online_admissions'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_name = db.Column(db.String(255), nullable=False)
    father_name = db.Column(db.String(255), nullable=False)
    mother_name = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.String(50), nullable=False)
    gender = db.Column(db.String(20), nullable=False)
    class_applied = db.Column(db.String(50), nullable=False)
    previous_school = db.Column(db.String(255))
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(255))
    student_photo = db.Column(db.String(255))
    aadhar_card = db.Column(db.String(255))
    previous_marksheet = db.Column(db.String(255))
    application_status = db.Column(db.String(50), default='Pending')
    admission_fee_paid = db.Column(db.Boolean, default=False)
    payment_receipt = db.Column(db.String(255))
    application_date = db.Column(db.DateTime, default=datetime.utcnow)

class FeePayment(db.Model):
    __tablename__ = 'fee_payments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_name = db.Column(db.String(255), nullable=False)
    admission_no = db.Column(db.String(100), nullable=False)
    class_name = db.Column(db.String(50), nullable=False)
    amount_paid = db.Column(db.Integer, nullable=False)
    payment_receipt = db.Column(db.String(255), nullable=False)
    payment_status = db.Column(db.String(50), default='Pending')
    payment_date = db.Column(db.DateTime, default=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(150), unique=True, nullable=False) # AdmissionNo for students, Phone for parents
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False) # 'admin', 'student', 'parent'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class ParentProfile(db.Model):
    __tablename__ = 'parent_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    father_name = db.Column(db.String(255), nullable=False)
    mother_name = db.Column(db.String(255), nullable=False)
    primary_phone = db.Column(db.String(20), unique=True, nullable=False)
    address = db.Column(db.Text)
    
    user = db.relationship('User', backref=db.backref('parent_profile', uselist=False))

class StudentProfile(db.Model):
    __tablename__ = 'student_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent_profiles.id'))
    admission_no = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    dob = db.Column(db.Date, nullable=False)
    gender = db.Column(db.String(20))
    current_class = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    roll_no = db.Column(db.String(50))
    photo_path = db.Column(db.String(255))
    qr_code_path = db.Column(db.String(255))
    
    user = db.relationship('User', backref=db.backref('student_profile', uselist=False))
    parent = db.relationship('ParentProfile', backref='children')

class AcademicResult(db.Model):
    __tablename__ = 'academic_results'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    term = db.Column(db.String(100), nullable=False) # e.g., 'Term 1 - 2026'
    subject_marks = db.Column(db.Text) # JSON string of subjects and marks {"Math": 85, "Science": 90}
    total_marks = db.Column(db.Integer)
    percentage = db.Column(db.Float)
    grade = db.Column(db.String(10))
    remarks = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    
    student = db.relationship('StudentProfile', backref='results')

class Assignment(db.Model):
    __tablename__ = 'assignments'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    target_class = db.Column(db.String(50), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255))
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TeacherProfile(db.Model):
    __tablename__ = 'teacher_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_code = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    subject = db.Column(db.String(100))
    assigned_classes = db.Column(db.Text) # Comma separated class names
    is_class_teacher = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('teacher_profile', uselist=False))

class StaffProfile(db.Model):
    __tablename__ = 'staff_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    employee_code = db.Column(db.String(100), unique=True, nullable=False)
    full_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20))
    designation = db.Column(db.String(100), default='Office Staff')
    permissions = db.Column(db.Text) # Comma separated keys: admissions,fees,students,attendance,website
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('staff_profile', uselist=False))

class StudentAttendance(db.Model):
    __tablename__ = 'student_attendance'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    attendance_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), nullable=False, default='Present') # Present, Absent, Late, Leave
    remarks = db.Column(db.Text)
    marked_by_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('StudentProfile', backref='attendance_records')
    marked_by = db.relationship('User', backref='marked_attendance_records')
    __table_args__ = (db.UniqueConstraint('student_id', 'attendance_date', name='uq_student_attendance_day'),)

class FeeInvoice(db.Model):
    __tablename__ = 'fee_invoices'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    paid_amount = db.Column(db.Integer, default=0)
    due_date = db.Column(db.Date)
    status = db.Column(db.String(50), default='Pending') # Pending, Partial, Paid, Overdue
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('StudentProfile', backref='fee_invoices')

class LeaveApplication(db.Model):
    __tablename__ = 'leave_applications'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    from_date = db.Column(db.Date, nullable=False)
    to_date = db.Column(db.Date, nullable=False)
    reason = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Pending') # Pending, Approved, Rejected
    admin_note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student = db.relationship('StudentProfile', backref='leave_applications')

class ParentMessage(db.Model):
    __tablename__ = 'parent_messages'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    parent_user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'))
    sender_role = db.Column(db.String(50), nullable=False) # parent, teacher, admin
    category = db.Column(db.String(100), default='General')
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), default='Open') # Open, Replied, Closed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    parent_user = db.relationship('User', foreign_keys=[parent_user_id], backref='parent_messages')
    student = db.relationship('StudentProfile', backref='messages')

class TransportRoute(db.Model):
    __tablename__ = 'transport_routes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    route_name = db.Column(db.String(255), nullable=False)
    vehicle_no = db.Column(db.String(100))
    driver_name = db.Column(db.String(255))
    driver_phone = db.Column(db.String(20))
    attendant_phone = db.Column(db.String(20))
    start_point = db.Column(db.String(255))
    end_point = db.Column(db.String(255))
    pickup_time = db.Column(db.String(50))
    drop_time = db.Column(db.String(50))
    live_tracking_url = db.Column(db.String(500))
    active = db.Column(db.Boolean, default=True)

class DriverProfile(db.Model):
    __tablename__ = 'driver_profiles'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('transport_routes.id'))
    driver_name = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(20), unique=True, nullable=False)
    license_no = db.Column(db.String(100))
    vehicle_no = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('driver_profile', uselist=False))
    route = db.relationship('TransportRoute', backref='drivers')

class BusLocation(db.Model):
    __tablename__ = 'bus_locations'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    driver_id = db.Column(db.Integer, db.ForeignKey('driver_profiles.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('transport_routes.id'))
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    speed = db.Column(db.Float)
    accuracy = db.Column(db.Float)
    address_hint = db.Column(db.String(255))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)

    driver = db.relationship('DriverProfile', backref='locations')
    route = db.relationship('TransportRoute', backref='locations')

class StudentTransport(db.Model):
    __tablename__ = 'student_transport'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student_profiles.id'), nullable=False)
    route_id = db.Column(db.Integer, db.ForeignKey('transport_routes.id'), nullable=False)
    pickup_point = db.Column(db.String(255))
    drop_point = db.Column(db.String(255))

    student = db.relationship('StudentProfile', backref=db.backref('transport_assignment', uselist=False))
    route = db.relationship('TransportRoute', backref='student_assignments')

class SchoolEvent(db.Model):
    __tablename__ = 'school_events'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    event_date = db.Column(db.Date, nullable=False)
    event_type = db.Column(db.String(100), default='General') # Holiday, Exam, Event, Meeting
    target_class = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class TimetableEntry(db.Model):
    __tablename__ = 'timetable_entries'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    class_name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10))
    weekday = db.Column(db.String(20), nullable=False)
    period_no = db.Column(db.Integer, nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    teacher_name = db.Column(db.String(255))
    starts_at = db.Column(db.String(20))
    ends_at = db.Column(db.String(20))

class DeviceToken(db.Model):
    __tablename__ = 'device_tokens'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    platform = db.Column(db.String(50), default='android')
    token = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='device_tokens')

class NotificationLog(db.Model):
    __tablename__ = 'notification_logs'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text)
    target_role = db.Column(db.String(50))
    target_class = db.Column(db.String(50))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    channel = db.Column(db.String(50), default='in_app')
    delivery_status = db.Column(db.String(50), default='Queued')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='notifications')
