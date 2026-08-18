from functools import wraps
from flask import session, redirect, url_for, flash

def role_required(*roles):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if not session.get('logged_in'):
                flash("Please log in to access this page.", "error")
                return redirect(url_for('auth.login'))
            
            if session.get('role') not in roles:
                flash("You do not have permission to access this page.", "error")
                return redirect(url_for('public.home'))
            
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

def admin_required(fn):
    return role_required('admin', 'staff_admin', 'staff')(fn)

def student_required(fn):
    return role_required('student')(fn)

def parent_required(fn):
    return role_required('parent')(fn)

def teacher_required(fn):
    return role_required('teacher')(fn)

def staff_required(fn):
    return role_required('staff', 'staff_admin')(fn)

def driver_required(fn):
    return role_required('driver')(fn)
