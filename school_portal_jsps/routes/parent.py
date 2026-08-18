from datetime import datetime
from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from decorators import parent_required
from extensions import db
from models import Assignment, BusLocation, FeeInvoice, LeaveApplication, ParentMessage, ParentProfile, SchoolEvent, StudentAttendance

parent_bp = Blueprint('parent', __name__, url_prefix='/parent')

def parse_date(value):
    return datetime.strptime(value, '%Y-%m-%d').date()

@parent_bp.route('/dashboard', methods=['GET', 'POST'])
@parent_required
def dashboard():
    parent = ParentProfile.query.filter_by(user_id=session.get('user_id')).first_or_404()

    if request.method == 'POST':
        action = request.form.get('action')
        student_id = int(request.form.get('student_id'))
        child_ids = {child.id for child in parent.children}
        if student_id not in child_ids:
            flash('Invalid student selected.', 'error')
            return redirect(url_for('parent.dashboard'))

        if action == 'leave':
            leave = LeaveApplication(
                student_id=student_id,
                from_date=parse_date(request.form.get('from_date')),
                to_date=parse_date(request.form.get('to_date')),
                reason=request.form.get('reason', ''),
            )
            db.session.add(leave)
            db.session.commit()
            flash('Leave application submitted.', 'success')
        elif action == 'message':
            msg = ParentMessage(
                parent_user_id=session.get('user_id'),
                student_id=student_id,
                sender_role='parent',
                category=request.form.get('category', 'General'),
                message=request.form.get('message', ''),
            )
            db.session.add(msg)
            db.session.commit()
            flash('Message sent to school.', 'success')
        return redirect(url_for('parent.dashboard'))
    
    # Get assignments for all children
    children_classes = [child.current_class for child in parent.children]
    assignments = []
    if children_classes:
        assignments = Assignment.query.filter(Assignment.target_class.in_(children_classes)).order_by(Assignment.due_date.desc()).limit(10).all()

    child_ids = [child.id for child in parent.children]
    fees = FeeInvoice.query.filter(FeeInvoice.student_id.in_(child_ids)).order_by(FeeInvoice.due_date.desc()).limit(10).all() if child_ids else []
    leaves = LeaveApplication.query.filter(LeaveApplication.student_id.in_(child_ids)).order_by(LeaveApplication.created_at.desc()).limit(10).all() if child_ids else []
    messages = ParentMessage.query.filter_by(parent_user_id=session.get('user_id')).order_by(ParentMessage.created_at.desc()).limit(10).all()
    attendance = StudentAttendance.query.filter(StudentAttendance.student_id.in_(child_ids)).order_by(StudentAttendance.attendance_date.desc()).limit(10).all() if child_ids else []
    events = SchoolEvent.query.order_by(SchoolEvent.event_date.asc()).limit(10).all()
    transport_locations = {}
    for child in parent.children:
        if child.transport_assignment and child.transport_assignment.route:
            last_location = BusLocation.query.filter_by(route_id=child.transport_assignment.route_id).order_by(BusLocation.recorded_at.desc()).first()
            transport_locations[child.id] = {
                'assignment': child.transport_assignment,
                'location': last_location,
            }

    return render_template('dashboards/parent.html', parent=parent, assignments=assignments, fees=fees, leaves=leaves, messages=messages, attendance=attendance, events=events, transport_locations=transport_locations)
