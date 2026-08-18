from datetime import datetime
import os

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename

from decorators import teacher_required
from extensions import db
from models import AcademicResult, Assignment, StudentAttendance, StudentProfile, TeacherProfile

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')


def parse_date(value):
    if not value:
        return None
    return datetime.strptime(value, '%Y-%m-%d').date()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'pdf', 'doc', 'docx'}


def current_teacher():
    return TeacherProfile.query.filter_by(user_id=session.get('user_id')).first_or_404()


def assigned_classes(teacher):
    if not teacher.assigned_classes:
        return []
    return [item.strip() for item in teacher.assigned_classes.split(',') if item.strip()]


@teacher_bp.route('/dashboard')
@teacher_required
def dashboard():
    teacher = current_teacher()
    classes = assigned_classes(teacher)
    students_count = StudentProfile.query.filter(StudentProfile.current_class.in_(classes)).count() if classes else 0
    assignments = Assignment.query.filter(Assignment.target_class.in_(classes)).order_by(Assignment.created_at.desc()).limit(8).all() if classes else []
    return render_template('teacher/dashboard.html', teacher=teacher, classes=classes, students_count=students_count, assignments=assignments)


@teacher_bp.route('/attendance', methods=['GET', 'POST'])
@teacher_required
def attendance():
    teacher = current_teacher()
    classes = assigned_classes(teacher)
    selected_class = request.values.get('class_name') or (classes[0] if classes else '')
    selected_date = request.values.get('attendance_date') or datetime.utcnow().strftime('%Y-%m-%d')

    if selected_class not in classes:
        flash('This class is not assigned to you.', 'error')
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        students = StudentProfile.query.filter_by(current_class=selected_class).all()
        for student in students:
            record = StudentAttendance.query.filter_by(student_id=student.id, attendance_date=parse_date(selected_date)).first()
            if not record:
                record = StudentAttendance(student_id=student.id, attendance_date=parse_date(selected_date), marked_by_user_id=session.get('user_id'))
                db.session.add(record)
            record.status = request.form.get(f'status_{student.id}', 'Present')
            record.remarks = request.form.get(f'remarks_{student.id}', '')
        db.session.commit()
        flash('Attendance saved.', 'success')
        return redirect(url_for('teacher.attendance', class_name=selected_class, attendance_date=selected_date))

    students = StudentProfile.query.filter_by(current_class=selected_class).order_by(StudentProfile.roll_no, StudentProfile.full_name).all()
    existing = StudentAttendance.query.filter_by(attendance_date=parse_date(selected_date)).all()
    records = {item.student_id: item for item in existing}
    return render_template('teacher/attendance.html', teacher=teacher, classes=classes, students=students, records=records, selected_class=selected_class, selected_date=selected_date)


@teacher_bp.route('/assignments', methods=['GET', 'POST'])
@teacher_required
def assignments():
    teacher = current_teacher()
    classes = assigned_classes(teacher)

    if request.method == 'POST':
        target_class = request.form.get('target_class', '')
        if target_class not in classes:
            flash('This class is not assigned to you.', 'error')
            return redirect(url_for('teacher.assignments'))

        file_path = ''
        file = request.files.get('file')
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            stamped = f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{filename}"
            file.save(os.path.join(current_app.config['ASSIGNMENTS_FOLDER'], stamped))
            file_path = f'assignments/{stamped}'

        assignment = Assignment(
            title=request.form.get('title', ''),
            description=request.form.get('description', ''),
            target_class=target_class,
            subject=request.form.get('subject') or teacher.subject or 'General',
            file_path=file_path,
            due_date=parse_date(request.form.get('due_date')),
        )
        db.session.add(assignment)
        db.session.commit()
        flash('Assignment posted.', 'success')
        return redirect(url_for('teacher.assignments'))

    items = Assignment.query.filter(Assignment.target_class.in_(classes)).order_by(Assignment.created_at.desc()).all() if classes else []
    return render_template('teacher/assignments.html', teacher=teacher, classes=classes, assignments=items)


@teacher_bp.route('/results', methods=['GET', 'POST'])
@teacher_required
def results():
    teacher = current_teacher()
    classes = assigned_classes(teacher)
    selected_class = request.values.get('class_name') or (classes[0] if classes else '')
    term = request.values.get('term', 'Term 1 - 2026')

    if selected_class not in classes:
        flash('This class is not assigned to you.', 'error')
        return redirect(url_for('teacher.dashboard'))

    if request.method == 'POST':
        student = StudentProfile.query.get_or_404(int(request.form.get('student_id')))
        if student.current_class not in classes:
            flash('This student is not assigned to you.', 'error')
            return redirect(url_for('teacher.results'))

        result = AcademicResult.query.filter_by(student_id=student.id, term=term).first()
        if not result:
            result = AcademicResult(student_id=student.id, term=term)
            db.session.add(result)
        result.subject_marks = request.form.get('subject_marks', '{}')
        result.total_marks = int(request.form.get('total_marks') or 0)
        result.percentage = float(request.form.get('percentage') or 0)
        result.grade = request.form.get('grade', '')
        result.remarks = request.form.get('remarks', '')
        result.is_published = bool(request.form.get('is_published'))
        db.session.commit()
        flash('Result saved.', 'success')
        return redirect(url_for('teacher.results', class_name=student.current_class, term=term))

    students = StudentProfile.query.filter_by(current_class=selected_class).order_by(StudentProfile.roll_no, StudentProfile.full_name).all()
    existing = AcademicResult.query.filter_by(term=term).all()
    results_by_student = {item.student_id: item for item in existing}
    return render_template('teacher/results.html', teacher=teacher, classes=classes, students=students, results=results_by_student, selected_class=selected_class, term=term)
