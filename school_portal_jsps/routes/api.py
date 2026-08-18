from datetime import datetime, timedelta
from functools import wraps
import json

import jwt
from flask import Blueprint, current_app, jsonify, request
from werkzeug.security import check_password_hash

from extensions import db
from models import (
    AcademicResult,
    Assignment,
    DeviceToken,
    Document,
    BusLocation,
    FeeInvoice,
    FeePayment,
    LeaveApplication,
    Notice,
    NotificationLog,
    ParentMessage,
    ParentProfile,
    SchoolEvent,
    StudentAttendance,
    StudentProfile,
    TimetableEntry,
    User,
)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')


def _date(value):
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d').date()


def _user_payload(user):
    name = user.username
    phone = ''
    if user.role == 'parent' and user.parent_profile:
        name = user.parent_profile.father_name
        phone = user.parent_profile.primary_phone
    elif user.role == 'student' and user.student_profile:
        name = user.student_profile.full_name
    elif user.role == 'teacher' and user.teacher_profile:
        name = user.teacher_profile.full_name
        phone = user.teacher_profile.phone

    return {
        'id': user.id,
        'name': name,
        'phone': phone,
        'role': user.role,
    }


def _make_token(user):
    expires = datetime.utcnow() + timedelta(hours=current_app.config['JWT_EXPIRY_HOURS'])
    payload = {
        'sub': str(user.id),
        'role': user.role,
        'exp': expires,
        'iat': datetime.utcnow(),
    }
    return jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')


def api_auth_required(*roles):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            header = request.headers.get('Authorization', '')
            token = header.replace('Bearer ', '', 1).strip() if header.startswith('Bearer ') else ''
            if not token:
                return jsonify({'error': 'Missing bearer token'}), 401
            try:
                payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            except jwt.ExpiredSignatureError:
                return jsonify({'error': 'Session expired'}), 401
            except jwt.InvalidTokenError:
                return jsonify({'error': 'Invalid token'}), 401

            user = User.query.filter_by(id=int(payload['sub']), is_active=True).first()
            if not user:
                return jsonify({'error': 'User not found'}), 401
            if roles and user.role not in roles:
                return jsonify({'error': 'Permission denied'}), 403

            request.current_user = user
            return fn(*args, **kwargs)

        return wrapper

    return decorator


def _student_allowed(student_id):
    user = request.current_user
    student = StudentProfile.query.get_or_404(student_id)
    if user.role == 'admin':
        return student
    if user.role == 'student' and student.user_id == user.id:
        return student
    if user.role == 'parent' and student.parent and student.parent.user_id == user.id:
        return student
    if user.role == 'teacher':
        assigned = []
        if user.teacher_profile and user.teacher_profile.assigned_classes:
            assigned = [item.strip() for item in user.teacher_profile.assigned_classes.split(',') if item.strip()]
        if student.current_class in assigned:
            return student
    return None


def _result_payload(result):
    try:
        subject_marks = json.loads(result.subject_marks or '{}')
    except json.JSONDecodeError:
        subject_marks = {}
    return {
        'id': result.id,
        'term': result.term,
        'subject_marks': subject_marks,
        'total_marks': result.total_marks,
        'percentage': result.percentage,
        'grade': result.grade,
        'remarks': result.remarks,
    }


@api_bp.route('/login', methods=['POST'])
def api_login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    role = data.get('role', 'parent')

    if not username or not password:
        return jsonify({'error': 'Missing credentials'}), 400

    user = User.query.filter_by(username=username, role=role, is_active=True).first()
    if user and check_password_hash(user.password_hash, password):
        return jsonify({
            'success': True,
            'token': _make_token(user),
            'user': _user_payload(user),
        }), 200

    return jsonify({'error': 'Invalid credentials'}), 401


@api_bp.route('/me', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def me():
    return jsonify({'user': _user_payload(request.current_user)}), 200


@api_bp.route('/parent/<int:user_id>/children', methods=['GET'])
@api_auth_required('parent', 'admin')
def get_children(user_id):
    user = request.current_user
    if user.role == 'parent' and user.id != user_id:
        return jsonify({'error': 'Permission denied'}), 403

    parent = ParentProfile.query.filter_by(user_id=user_id).first()
    if not parent:
        return jsonify({'error': 'Parent not found'}), 404

    children_data = [{
        'id': child.id,
        'admission_no': child.admission_no,
        'name': child.full_name,
        'class': f"{child.current_class} {child.section or ''}".strip(),
        'class_name': f"{child.current_class} {child.section or ''}".strip(),
        'raw_class': child.current_class,
        'section': child.section,
        'dob': child.dob.strftime('%Y-%m-%d'),
    } for child in parent.children]

    return jsonify({'children': children_data}), 200


@api_bp.route('/notices', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def get_notices():
    notices = Notice.query.order_by(Notice.date.desc()).limit(25).all()
    notices_data = [{
        'id': n.id,
        'title': n.title,
        'content': n.content,
        'date': n.date.strftime('%Y-%m-%d'),
    } for n in notices]

    return jsonify({'notices': notices_data}), 200


@api_bp.route('/assignments/<string:target_class>', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def get_assignments(target_class):
    assignments = Assignment.query.filter_by(target_class=target_class).order_by(Assignment.due_date.desc()).all()
    assignments_data = [{
        'id': a.id,
        'title': a.title,
        'description': a.description,
        'subject': a.subject,
        'target_class': a.target_class,
        'due_date': a.due_date.strftime('%Y-%m-%d') if a.due_date else None,
        'file_path': a.file_path,
    } for a in assignments]

    return jsonify({'assignments': assignments_data}), 200


@api_bp.route('/student/<int:student_id>/results', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def get_results(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    results_data = [_result_payload(r) for r in student.results if r.is_published]
    return jsonify({'results': results_data}), 200


@api_bp.route('/student/<int:student_id>/attendance', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def get_attendance(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    month = request.args.get('month')
    query = StudentAttendance.query.filter_by(student_id=student.id)
    if month:
        start = datetime.strptime(month + '-01', '%Y-%m-%d').date()
        end = (start.replace(day=28) + timedelta(days=4)).replace(day=1)
        query = query.filter(StudentAttendance.attendance_date >= start, StudentAttendance.attendance_date < end)

    records = query.order_by(StudentAttendance.attendance_date.desc()).all()
    summary = {'Present': 0, 'Absent': 0, 'Late': 0, 'Leave': 0}
    data = []
    for item in records:
        summary[item.status] = summary.get(item.status, 0) + 1
        data.append({
            'id': item.id,
            'date': item.attendance_date.strftime('%Y-%m-%d'),
            'status': item.status,
            'remarks': item.remarks,
        })

    return jsonify({'attendance': data, 'summary': summary}), 200


@api_bp.route('/student/<int:student_id>/fees', methods=['GET'])
@api_auth_required('parent', 'student', 'admin')
def get_fees(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    invoices = FeeInvoice.query.filter_by(student_id=student.id).order_by(FeeInvoice.due_date.desc()).all()
    payments = FeePayment.query.filter_by(admission_no=student.admission_no).order_by(FeePayment.payment_date.desc()).all()
    return jsonify({
        'invoices': [{
            'id': item.id,
            'title': item.title,
            'amount': item.amount,
            'paid_amount': item.paid_amount,
            'due_date': item.due_date.strftime('%Y-%m-%d') if item.due_date else None,
            'status': item.status,
            'notes': item.notes,
        } for item in invoices],
        'payments': [{
            'id': item.id,
            'amount_paid': item.amount_paid,
            'status': item.payment_status,
            'receipt': item.payment_receipt,
            'date': item.payment_date.strftime('%Y-%m-%d'),
        } for item in payments],
    }), 200


@api_bp.route('/student/<int:student_id>/leave', methods=['GET', 'POST'])
@api_auth_required('parent', 'student', 'admin')
def leave_applications(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    if request.method == 'POST':
        data = request.get_json() or {}
        leave = LeaveApplication(
            student_id=student.id,
            from_date=_date(data.get('from_date')),
            to_date=_date(data.get('to_date')),
            reason=data.get('reason', '').strip(),
        )
        if not leave.from_date or not leave.to_date or not leave.reason:
            return jsonify({'error': 'from_date, to_date and reason are required'}), 400
        db.session.add(leave)
        db.session.commit()
        return jsonify({'success': True, 'id': leave.id}), 201

    leaves = LeaveApplication.query.filter_by(student_id=student.id).order_by(LeaveApplication.created_at.desc()).all()
    return jsonify({'leaves': [{
        'id': item.id,
        'from_date': item.from_date.strftime('%Y-%m-%d'),
        'to_date': item.to_date.strftime('%Y-%m-%d'),
        'reason': item.reason,
        'status': item.status,
        'admin_note': item.admin_note,
    } for item in leaves]}), 200


@api_bp.route('/student/<int:student_id>/transport', methods=['GET'])
@api_auth_required('parent', 'student', 'admin')
def get_transport(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    assignment = student.transport_assignment
    if not assignment:
        return jsonify({'transport': None}), 200
    route = assignment.route
    last_location = BusLocation.query.filter_by(route_id=assignment.route_id).order_by(BusLocation.recorded_at.desc()).first()
    return jsonify({'transport': {
        'route_name': route.route_name,
        'vehicle_no': route.vehicle_no,
        'driver_name': route.driver_name,
        'driver_phone': route.driver_phone,
        'attendant_phone': route.attendant_phone,
        'pickup_point': assignment.pickup_point,
        'drop_point': assignment.drop_point,
        'pickup_time': route.pickup_time,
        'drop_time': route.drop_time,
        'live_tracking_url': route.live_tracking_url,
        'last_latitude': last_location.latitude if last_location else None,
        'last_longitude': last_location.longitude if last_location else None,
        'last_updated': last_location.recorded_at.strftime('%Y-%m-%d %H:%M') if last_location else None,
    }}), 200


@api_bp.route('/student/<int:student_id>/calendar', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def get_calendar(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    events = SchoolEvent.query.filter(
        (SchoolEvent.target_class == None) | (SchoolEvent.target_class == '') | (SchoolEvent.target_class == student.current_class)
    ).order_by(SchoolEvent.event_date.asc()).limit(60).all()
    timetable = TimetableEntry.query.filter_by(class_name=student.current_class).order_by(TimetableEntry.weekday, TimetableEntry.period_no).all()
    return jsonify({
        'events': [{
            'id': item.id,
            'title': item.title,
            'description': item.description,
            'date': item.event_date.strftime('%Y-%m-%d'),
            'event_type': item.event_type,
            'target_class': item.target_class,
        } for item in events],
        'timetable': [{
            'id': item.id,
            'weekday': item.weekday,
            'period_no': item.period_no,
            'subject': item.subject,
            'teacher_name': item.teacher_name,
            'starts_at': item.starts_at,
            'ends_at': item.ends_at,
        } for item in timetable],
    }), 200


@api_bp.route('/student/<int:student_id>/messages', methods=['GET', 'POST'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def student_messages(student_id):
    student = _student_allowed(student_id)
    if not student:
        return jsonify({'error': 'Permission denied'}), 403

    if request.method == 'POST':
        data = request.get_json() or {}
        parent_user_id = student.parent.user_id if student.parent else request.current_user.id
        msg = ParentMessage(
            parent_user_id=parent_user_id,
            student_id=student.id,
            sender_role=request.current_user.role,
            category=data.get('category', 'General'),
            message=data.get('message', '').strip(),
        )
        if not msg.message:
            return jsonify({'error': 'message is required'}), 400
        db.session.add(msg)
        db.session.commit()
        return jsonify({'success': True, 'id': msg.id}), 201

    messages = ParentMessage.query.filter_by(student_id=student.id).order_by(ParentMessage.created_at.desc()).limit(50).all()
    return jsonify({'messages': [{
        'id': item.id,
        'sender_role': item.sender_role,
        'category': item.category,
        'message': item.message,
        'status': item.status,
        'date': item.created_at.strftime('%Y-%m-%d %H:%M'),
    } for item in messages]}), 200


@api_bp.route('/documents', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def documents():
    category = request.args.get('category')
    query = Document.query
    if category:
        query = query.filter_by(category=category)
    docs = query.order_by(Document.id.desc()).limit(100).all()
    return jsonify({'documents': [{
        'id': item.id,
        'title': item.title,
        'category': item.category,
        'file_path': item.file_path,
    } for item in docs]}), 200


@api_bp.route('/notifications', methods=['GET'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def notifications():
    user = request.current_user
    logs = NotificationLog.query.filter(
        (NotificationLog.user_id == None) | (NotificationLog.user_id == user.id) | (NotificationLog.target_role == user.role)
    ).order_by(NotificationLog.created_at.desc()).limit(50).all()
    return jsonify({'notifications': [{
        'id': item.id,
        'title': item.title,
        'body': item.body,
        'channel': item.channel,
        'delivery_status': item.delivery_status,
        'date': item.created_at.strftime('%Y-%m-%d %H:%M'),
    } for item in logs]}), 200


@api_bp.route('/devices', methods=['POST'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def register_device():
    data = request.get_json() or {}
    token = data.get('token', '').strip()
    if not token:
        return jsonify({'error': 'token is required'}), 400

    device = DeviceToken.query.filter_by(user_id=request.current_user.id, token=token).first()
    if not device:
        device = DeviceToken(
            user_id=request.current_user.id,
            platform=data.get('platform', 'android'),
            token=token,
        )
        db.session.add(device)
        db.session.commit()
    return jsonify({'success': True}), 200


@api_bp.route('/assistant/ask', methods=['POST'])
@api_auth_required('parent', 'student', 'teacher', 'admin')
def assistant_answer():
    data = request.get_json() or {}
    question = data.get('question', '').lower()
    if 'fee' in question:
        answer = 'Fee details are available in the Fees section. Pending invoices and submitted receipts are shown there.'
    elif 'attendance' in question or 'absent' in question:
        answer = 'Attendance is updated from the school dashboard. Open Attendance to see daily status and monthly summary.'
    elif 'homework' in question or 'assignment' in question:
        answer = 'Homework and study materials are available class-wise in the Assignments section.'
    elif 'transport' in question or 'bus' in question:
        answer = 'Transport route, driver details, and pickup/drop information are available in the Transport section.'
    else:
        answer = 'Your query has been noted. For urgent help, please send a message to the school from the Messages section.'
    return jsonify({'answer': answer}), 200
