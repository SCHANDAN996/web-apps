from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash
from extensions import db
from models import User, StudentProfile, ParentProfile, AcademicResult
from decorators import admin_required
from datetime import datetime

admin_auto_bp = Blueprint('admin_auto', __name__, url_prefix='/admin')

@admin_auto_bp.route('/student_draft', methods=['GET', 'POST'])
@admin_required
def student_draft():
    if request.method == 'POST':
        admission_no = request.form.get('admission_no')
        student_name = request.form.get('student_name')
        dob_str = request.form.get('dob') # Format YYYY-MM-DD
        gender = request.form.get('gender')
        current_class = request.form.get('current_class')
        section = request.form.get('section', '')
        
        father_name = request.form.get('father_name')
        mother_name = request.form.get('mother_name')
        phone = request.form.get('phone')
        
        # Check if student already exists
        if StudentProfile.query.filter_by(admission_no=admission_no).first():
            flash('Student with this Admission No already exists!', 'error')
            return redirect(url_for('admin_auto.student_draft'))
            
        try:
            dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            # Student Password = DOB (DDMMYYYY)
            student_password = dob.strftime('%d%m%Y')
            
            # Parent Password = 'jsps' + last 4 of phone
            parent_password = 'jsps' + phone[-4:] if len(phone) >= 4 else 'jsps1234'
            
            # 1. Create Parent User (if not exists by phone)
            parent_user = User.query.filter_by(username=phone, role='parent').first()
            if not parent_user:
                parent_user = User(
                    username=phone, 
                    password_hash=generate_password_hash(parent_password),
                    role='parent'
                )
                db.session.add(parent_user)
                db.session.flush() # Get user ID
                
                parent_profile = ParentProfile(
                    user_id=parent_user.id,
                    father_name=father_name,
                    mother_name=mother_name,
                    primary_phone=phone
                )
                db.session.add(parent_profile)
                db.session.flush()
            else:
                parent_profile = parent_user.parent_profile
                
            # 2. Create Student User
            student_user = User(
                username=admission_no,
                password_hash=generate_password_hash(student_password),
                role='student'
            )
            db.session.add(student_user)
            db.session.flush()
            
            # 3. Create Student Profile
            student_profile = StudentProfile(
                user_id=student_user.id,
                parent_id=parent_profile.id,
                admission_no=admission_no,
                full_name=student_name,
                dob=dob,
                gender=gender,
                current_class=current_class,
                section=section
            )
            db.session.add(student_profile)
            db.session.flush()
            
            # 4. Generate Blank Academic Result (Term 1)
            blank_result = AcademicResult(
                student_id=student_profile.id,
                term='Term 1 - 2026',
                subject_marks='{}',
                is_published=False
            )
            db.session.add(blank_result)
            
            db.session.commit()
            
            flash(f'Student {student_name} enrolled successfully! Student Password: {student_password}, Parent Password: {parent_password}', 'success')
            return redirect(url_for('admin_auto.manage_students'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error enrolling student: {str(e)}', 'error')
            
    return render_template('admin/student_draft.html')

@admin_auto_bp.route('/students')
@admin_required
def manage_students():
    students = StudentProfile.query.order_by(StudentProfile.id.desc()).all()
    return render_template('admin/manage_students.html', students=students)

@admin_auto_bp.route('/student_edit/<int:student_id>', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    if request.method == 'POST':
        student.full_name = request.form.get('student_name')
        student.current_class = request.form.get('current_class')
        student.section = request.form.get('section', '')
        
        dob_str = request.form.get('dob')
        if dob_str:
            student.dob = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
        student.gender = request.form.get('gender')
        
        if student.parent:
            student.parent.father_name = request.form.get('father_name')
            student.parent.mother_name = request.form.get('mother_name')
            
        db.session.commit()
        flash('Student details updated successfully!', 'success')
        return redirect(url_for('admin_auto.manage_students'))
        
    return render_template('admin/student_edit.html', student=student)

@admin_auto_bp.route('/promote_students', methods=['GET', 'POST'])
@admin_required
def promote_students():
    if request.method == 'POST':
        from_class = request.form.get('from_class')
        to_class = request.form.get('to_class')
        
        if not from_class or not to_class:
            flash('Please select both From and To classes.', 'error')
            return redirect(url_for('admin_auto.promote_students'))
            
        students_to_promote = StudentProfile.query.filter_by(current_class=from_class).all()
        count = 0
        for s in students_to_promote:
            s.current_class = to_class
            count += 1
            
        db.session.commit()
        flash(f'Successfully promoted {count} students from {from_class} to {to_class}.', 'success')
        return redirect(url_for('admin_auto.manage_students'))
        
    return render_template('admin/promote_students.html')

@admin_auto_bp.route('/id_card/<int:student_id>')
@admin_required
def generate_id_card(student_id):
    student = StudentProfile.query.get_or_404(student_id)
    return render_template('admin/id_card_template.html', student=student)

import io
import zipfile
from flask import send_file

@admin_auto_bp.route('/bulk_download_ids', methods=['POST'])
@admin_required
def bulk_download_ids():
    class_name = request.form.get('class_name')
    students = StudentProfile.query.filter_by(current_class=class_name).all()
    
    if not students:
        flash(f'No students found in {class_name}', 'error')
        return redirect(url_for('admin_auto.manage_students'))
        
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for student in students:
            html_content = render_template('admin/id_card_template.html', student=student)
            file_name = f"IDCard_{student.admission_no}_{student.full_name.replace(' ', '_')}.html"
            zf.writestr(file_name, html_content)
            
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'ID_Cards_{class_name}.zip'
    )

@admin_auto_bp.route('/bulk_download_results', methods=['POST'])
@admin_required
def bulk_download_results():
    class_name = request.form.get('class_name')
    students = StudentProfile.query.filter_by(current_class=class_name).all()
    
    if not students:
        flash(f'No students found in {class_name}', 'error')
        return redirect(url_for('admin_auto.manage_students'))
        
    memory_file = io.BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        for student in students:
            # We assume a basic result html representation or we just use a generic format
            # Let's create a simple HTML for result since there's no result template yet
            results_html = "<h1>Academic Results</h1><hr>"
            for r in student.results:
                results_html += f"<h3>{r.term}</h3><p>Grade: {r.grade} | Percentage: {r.percentage}%</p>"
            
            html_content = f"<html><body><h2>Result for {student.full_name} ({student.admission_no})</h2>{results_html}</body></html>"
            
            file_name = f"Result_{student.admission_no}_{student.full_name.replace(' ', '_')}.html"
            zf.writestr(file_name, html_content)
            
    memory_file.seek(0)
    return send_file(
        memory_file,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'Results_{class_name}.zip'
    )
