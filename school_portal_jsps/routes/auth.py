from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.security import check_password_hash
from extensions import db
from models import User

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role') # 'admin', 'student', 'parent'
        
        # Super Admin Check (from config)
        if role == 'admin' and username == current_app.config['ADMIN_USERNAME']:
            if check_password_hash(current_app.config['ADMIN_PASSWORD_HASH'], password):
                session['logged_in'] = True
                session['role'] = 'admin'
                session['user_id'] = 0
                flash('Logged in successfully as Admin!', 'success')
                return redirect(url_for('admin.admin_dashboard'))
                
        # Database User Check
        if role == 'staff':
            user = User.query.filter(User.username == username, User.role.in_(['staff', 'staff_admin']), User.is_active == True).first()
        else:
            user = User.query.filter_by(username=username, role=role, is_active=True).first()
        if user and check_password_hash(user.password_hash, password):
            session['logged_in'] = True
            session['role'] = user.role
            session['user_id'] = user.id
            flash(f'Logged in successfully as {user.role.capitalize()}!', 'success')
            
            if user.role == 'student':
                return redirect(url_for('student.dashboard'))
            elif user.role == 'parent':
                return redirect(url_for('parent.dashboard'))
            elif user.role == 'teacher':
                return redirect(url_for('teacher.dashboard'))
            elif user.role in ('staff', 'staff_admin'):
                return redirect(url_for('staff.dashboard'))
            elif user.role == 'driver':
                return redirect(url_for('driver.dashboard'))
            elif user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
                
        flash('Invalid username, password, or role', 'error')
        
    return render_template('auth/unified_login.html')

@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('public.home'))
