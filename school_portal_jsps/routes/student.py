from flask import Blueprint, render_template, session
from decorators import student_required
from models import FeeInvoice, SchoolEvent, StudentAttendance, StudentProfile, Assignment

student_bp = Blueprint('student', __name__, url_prefix='/student')

@student_bp.route('/dashboard')
@student_required
def dashboard():
    student = StudentProfile.query.filter_by(user_id=session.get('user_id')).first_or_404()
    
    # Fetch assignments for the student's class
    assignments = Assignment.query.filter_by(target_class=student.current_class).order_by(Assignment.due_date.desc()).all()
    fees = FeeInvoice.query.filter_by(student_id=student.id).order_by(FeeInvoice.due_date.desc()).limit(6).all()
    attendance = StudentAttendance.query.filter_by(student_id=student.id).order_by(StudentAttendance.attendance_date.desc()).limit(10).all()
    events = SchoolEvent.query.order_by(SchoolEvent.event_date.asc()).limit(10).all()
    
    return render_template('dashboards/student.html', student=student, assignments=assignments, fees=fees, attendance=attendance, events=events)
