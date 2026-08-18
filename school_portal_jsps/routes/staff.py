from flask import Blueprint, render_template, session

from decorators import staff_required
from models import AdmissionInquiry, FeeInvoice, FeePayment, OnlineAdmission, ParentMessage, StaffProfile, StudentProfile

staff_bp = Blueprint('staff', __name__, url_prefix='/staff')


def current_staff():
    return StaffProfile.query.filter_by(user_id=session.get('user_id')).first()


@staff_bp.route('/dashboard')
@staff_required
def dashboard():
    staff = current_staff()
    permissions = []
    if staff and staff.permissions:
        permissions = [item.strip() for item in staff.permissions.split(',') if item.strip()]

    stats = {
        'students': StudentProfile.query.count(),
        'online_admissions': OnlineAdmission.query.filter_by(application_status='Pending').count(),
        'admission_inquiries': AdmissionInquiry.query.count(),
        'pending_fees': FeeInvoice.query.filter(FeeInvoice.status.in_(['Pending', 'Partial', 'Overdue'])).count(),
        'fee_receipts': FeePayment.query.filter_by(payment_status='Pending').count(),
        'open_messages': ParentMessage.query.filter_by(status='Open').count(),
    }
    return render_template('staff/dashboard.html', staff=staff, permissions=permissions, stats=stats)
