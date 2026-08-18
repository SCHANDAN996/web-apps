from datetime import datetime
import json

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from werkzeug.security import generate_password_hash

from decorators import admin_required
from extensions import db
from models import (
    AcademicResult,
    FeeInvoice,
    LeaveApplication,
    NotificationLog,
    ParentMessage,
    SchoolEvent,
    StudentAttendance,
    StudentProfile,
    StudentTransport,
    TeacherProfile,
    TimetableEntry,
    TransportRoute,
    User,
)

admin_erp_bp = Blueprint('admin_erp', __name__, url_prefix='/admin')


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d').date()


def current_marker_id():
    user_id = session.get('user_id')
    return user_id if user_id and user_id > 0 else None


@admin_erp_bp.route('/attendance', methods=['GET', 'POST'])
@admin_required
def attendance():
    selected_class = request.values.get('class_name', '')
    selected_date = request.values.get('attendance_date') or datetime.utcnow().strftime('%Y-%m-%d')

    if request.method == 'POST':
        students = StudentProfile.query.filter_by(current_class=selected_class).all()
        for student in students:
            status = request.form.get(f'status_{student.id}', 'Present')
            remarks = request.form.get(f'remarks_{student.id}', '')
            record = StudentAttendance.query.filter_by(
                student_id=student.id,
                attendance_date=parse_date(selected_date),
            ).first()
            if not record:
                record = StudentAttendance(
                    student_id=student.id,
                    attendance_date=parse_date(selected_date),
                    marked_by_user_id=current_marker_id(),
                )
                db.session.add(record)
            record.status = status
            record.remarks = remarks
        db.session.commit()
        flash('Attendance saved successfully.', 'success')
        return redirect(url_for('admin_erp.attendance', class_name=selected_class, attendance_date=selected_date))

    classes = [row[0] for row in db.session.query(StudentProfile.current_class).distinct().order_by(StudentProfile.current_class).all()]
    students = []
    records = {}
    if selected_class:
        students = StudentProfile.query.filter_by(current_class=selected_class).order_by(StudentProfile.roll_no, StudentProfile.full_name).all()
        day = parse_date(selected_date)
        existing = StudentAttendance.query.filter_by(attendance_date=day).all()
        records = {item.student_id: item for item in existing}

    return render_template('admin/erp_attendance.html', classes=classes, students=students, records=records, selected_class=selected_class, selected_date=selected_date)


@admin_erp_bp.route('/fee-invoices', methods=['GET', 'POST'])
@admin_required
def fee_invoices():
    if request.method == 'POST':
        student = StudentProfile.query.filter_by(admission_no=request.form.get('admission_no', '').strip()).first()
        if not student:
            flash('Student admission number not found.', 'error')
            return redirect(url_for('admin_erp.fee_invoices'))

        invoice = FeeInvoice(
            student_id=student.id,
            title=request.form.get('title', '').strip(),
            amount=int(request.form.get('amount') or 0),
            paid_amount=int(request.form.get('paid_amount') or 0),
            due_date=parse_date(request.form.get('due_date')),
            status=request.form.get('status', 'Pending'),
            notes=request.form.get('notes', ''),
        )
        db.session.add(invoice)
        db.session.commit()
        flash('Fee invoice added successfully.', 'success')
        return redirect(url_for('admin_erp.fee_invoices'))

    invoices = FeeInvoice.query.order_by(FeeInvoice.created_at.desc()).all()
    return render_template('admin/erp_fee_invoices.html', invoices=invoices)


@admin_erp_bp.route('/exam-results', methods=['GET', 'POST'])
@admin_required
def exam_results():
    selected_class = request.values.get('class_name', '')
    selected_term = request.values.get('term', 'Term 1 - 2026')

    if request.method == 'POST':
        student = StudentProfile.query.get_or_404(int(request.form.get('student_id')))
        term = request.form.get('term', selected_term)
        result = AcademicResult.query.filter_by(student_id=student.id, term=term).first()
        if not result:
            result = AcademicResult(student_id=student.id, term=term)
            db.session.add(result)

        subject_marks = request.form.get('subject_marks', '{}')
        try:
            json.loads(subject_marks)
        except json.JSONDecodeError:
            flash('Subject marks must be valid JSON, for example {"Math": 90, "Science": 85}.', 'error')
            return redirect(url_for('admin_erp.exam_results', class_name=student.current_class, term=term))

        result.subject_marks = subject_marks
        result.total_marks = int(request.form.get('total_marks') or 0)
        result.percentage = float(request.form.get('percentage') or 0)
        result.grade = request.form.get('grade', '')
        result.remarks = request.form.get('remarks', '')
        result.is_published = bool(request.form.get('is_published'))
        db.session.commit()
        flash('Result saved successfully.', 'success')
        return redirect(url_for('admin_erp.exam_results', class_name=student.current_class, term=term))

    classes = [row[0] for row in db.session.query(StudentProfile.current_class).distinct().order_by(StudentProfile.current_class).all()]
    students = []
    results = {}
    if selected_class:
        students = StudentProfile.query.filter_by(current_class=selected_class).order_by(StudentProfile.roll_no, StudentProfile.full_name).all()
        existing = AcademicResult.query.filter_by(term=selected_term).all()
        results = {item.student_id: item for item in existing}

    return render_template('admin/erp_exam_results.html', classes=classes, students=students, results=results, selected_class=selected_class, selected_term=selected_term)


@admin_erp_bp.route('/transport', methods=['GET', 'POST'])
@admin_required
def transport():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_route':
            route = TransportRoute(
                route_name=request.form.get('route_name', '').strip(),
                vehicle_no=request.form.get('vehicle_no', ''),
                driver_name=request.form.get('driver_name', ''),
                driver_phone=request.form.get('driver_phone', ''),
                attendant_phone=request.form.get('attendant_phone', ''),
                start_point=request.form.get('start_point', ''),
                end_point=request.form.get('end_point', ''),
                pickup_time=request.form.get('pickup_time', ''),
                drop_time=request.form.get('drop_time', ''),
                live_tracking_url=request.form.get('live_tracking_url', ''),
            )
            db.session.add(route)
            db.session.commit()
            flash('Transport route added.', 'success')
        elif action == 'assign_student':
            student = StudentProfile.query.filter_by(admission_no=request.form.get('admission_no', '').strip()).first()
            route = TransportRoute.query.get(request.form.get('route_id'))
            if student and route:
                assignment = StudentTransport.query.filter_by(student_id=student.id).first()
                if not assignment:
                    assignment = StudentTransport(student_id=student.id, route_id=route.id)
                    db.session.add(assignment)
                assignment.route_id = route.id
                assignment.pickup_point = request.form.get('pickup_point', '')
                assignment.drop_point = request.form.get('drop_point', '')
                db.session.commit()
                flash('Student transport assigned.', 'success')
            else:
                flash('Student or route not found.', 'error')
        return redirect(url_for('admin_erp.transport'))

    routes = TransportRoute.query.order_by(TransportRoute.route_name).all()
    assignments = StudentTransport.query.order_by(StudentTransport.id.desc()).all()
    return render_template('admin/erp_transport.html', routes=routes, assignments=assignments)


@admin_erp_bp.route('/school-calendar', methods=['GET', 'POST'])
@admin_required
def school_calendar():
    if request.method == 'POST':
        event = SchoolEvent(
            title=request.form.get('title', '').strip(),
            description=request.form.get('description', ''),
            event_date=parse_date(request.form.get('event_date')),
            event_type=request.form.get('event_type', 'General'),
            target_class=request.form.get('target_class', ''),
        )
        db.session.add(event)
        db.session.commit()
        flash('Calendar event added.', 'success')
        return redirect(url_for('admin_erp.school_calendar'))

    events = SchoolEvent.query.order_by(SchoolEvent.event_date.desc()).all()
    return render_template('admin/erp_calendar.html', events=events)


@admin_erp_bp.route('/timetable', methods=['GET', 'POST'])
@admin_required
def timetable():
    if request.method == 'POST':
        entry = TimetableEntry(
            class_name=request.form.get('class_name', '').strip(),
            section=request.form.get('section', ''),
            weekday=request.form.get('weekday', ''),
            period_no=int(request.form.get('period_no') or 1),
            subject=request.form.get('subject', ''),
            teacher_name=request.form.get('teacher_name', ''),
            starts_at=request.form.get('starts_at', ''),
            ends_at=request.form.get('ends_at', ''),
        )
        db.session.add(entry)
        db.session.commit()
        flash('Timetable entry added.', 'success')
        return redirect(url_for('admin_erp.timetable'))

    entries = TimetableEntry.query.order_by(TimetableEntry.class_name, TimetableEntry.weekday, TimetableEntry.period_no).all()
    return render_template('admin/erp_timetable.html', entries=entries)


@admin_erp_bp.route('/leave-requests')
@admin_required
def leave_requests():
    leaves = LeaveApplication.query.order_by(LeaveApplication.created_at.desc()).all()
    return render_template('admin/erp_leave.html', leaves=leaves)


@admin_erp_bp.route('/leave-requests/<int:leave_id>/<string:decision>', methods=['POST'])
@admin_required
def decide_leave(leave_id, decision):
    leave = LeaveApplication.query.get_or_404(leave_id)
    leave.status = 'Approved' if decision == 'approve' else 'Rejected'
    leave.admin_note = request.form.get('admin_note', '')
    db.session.commit()
    flash(f'Leave request {leave.status.lower()}.', 'success')
    return redirect(url_for('admin_erp.leave_requests'))


@admin_erp_bp.route('/messages', methods=['GET', 'POST'])
@admin_required
def messages():
    if request.method == 'POST':
        original = ParentMessage.query.get_or_404(int(request.form.get('message_id')))
        reply = ParentMessage(
            parent_user_id=original.parent_user_id,
            student_id=original.student_id,
            sender_role='admin',
            category='Reply',
            message=request.form.get('message', '').strip(),
            status='Replied',
        )
        original.status = 'Replied'
        db.session.add(reply)
        db.session.commit()
        flash('Reply sent in parent message thread.', 'success')
        return redirect(url_for('admin_erp.messages'))

    messages = ParentMessage.query.order_by(ParentMessage.created_at.desc()).all()
    return render_template('admin/erp_messages.html', messages=messages)


@admin_erp_bp.route('/teachers', methods=['GET', 'POST'])
@admin_required
def teachers():
    if request.method == 'POST':
        employee_code = request.form.get('employee_code', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password') or ('jsps' + phone[-4:])
        if User.query.filter_by(username=employee_code, role='teacher').first():
            flash('Teacher employee code already exists.', 'error')
            return redirect(url_for('admin_erp.teachers'))

        user = User(username=employee_code, password_hash=generate_password_hash(password), role='teacher')
        db.session.add(user)
        db.session.flush()
        profile = TeacherProfile(
            user_id=user.id,
            employee_code=employee_code,
            full_name=request.form.get('full_name', ''),
            phone=phone,
            subject=request.form.get('subject', ''),
            assigned_classes=request.form.get('assigned_classes', ''),
            is_class_teacher=bool(request.form.get('is_class_teacher')),
        )
        db.session.add(profile)
        db.session.commit()
        flash(f'Teacher account created. Login ID: {employee_code}, Password: {password}', 'success')
        return redirect(url_for('admin_erp.teachers'))

    teachers = TeacherProfile.query.order_by(TeacherProfile.full_name).all()
    return render_template('admin/erp_teachers.html', teachers=teachers)


@admin_erp_bp.route('/notifications', methods=['GET', 'POST'])
@admin_required
def notifications():
    if request.method == 'POST':
        log = NotificationLog(
            title=request.form.get('title', '').strip(),
            body=request.form.get('body', ''),
            target_role=request.form.get('target_role', ''),
            target_class=request.form.get('target_class', ''),
            channel=request.form.get('channel', 'in_app'),
            delivery_status='Queued',
        )
        db.session.add(log)
        db.session.commit()
        flash('Notification queued for in-app delivery. Connect FCM/SMS keys to send outside the app.', 'success')
        return redirect(url_for('admin_erp.notifications'))

    logs = NotificationLog.query.order_by(NotificationLog.created_at.desc()).all()
    return render_template('admin/erp_notifications.html', logs=logs)
