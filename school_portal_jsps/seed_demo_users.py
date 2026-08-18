import os
from datetime import date

from werkzeug.security import generate_password_hash

from extensions import db
from models import (
    AcademicResult,
    DriverProfile,
    ParentProfile,
    StaffProfile,
    StudentProfile,
    StudentTransport,
    TeacherProfile,
    TransportRoute,
    User,
)


def _env(name, default):
    return os.environ.get(name, default)


def _user(username, password, role):
    user = User.query.filter_by(username=username, role=role).first()
    if user:
        return user
    user = User(username=username, password_hash=generate_password_hash(password), role=role, is_active=True)
    db.session.add(user)
    db.session.flush()
    return user


def seed_demo_users():
    if _env('AUTO_SEED_TEST_USERS', '1') != '1':
        return

    _user(_env('TEST_SUPER_ADMIN_USERNAME', 'admin'), _env('TEST_SUPER_ADMIN_PASSWORD', 'jsps@admin123'), 'admin')

    route = TransportRoute.query.filter_by(route_name='Demo Route 1').first()
    if not route:
        route = TransportRoute(
            route_name='Demo Route 1',
            vehicle_no='UP67 JS 1001',
            driver_name='Demo Driver',
            driver_phone='9000000004',
            attendant_phone='9000000005',
            start_point='Mughalsarai',
            end_point='JS Public School Campus',
            pickup_time='07:15 AM',
            drop_time='02:15 PM',
            live_tracking_url='',
        )
        db.session.add(route)
        db.session.flush()

    staff_admin_user = _user(_env('TEST_SECOND_ADMIN_USERNAME', 'schooladmin'), _env('TEST_SECOND_ADMIN_PASSWORD', 'school@123'), 'staff_admin')
    if not staff_admin_user.staff_profile:
        db.session.add(StaffProfile(
            user_id=staff_admin_user.id,
            employee_code=staff_admin_user.username,
            full_name='Second Admin',
            phone='9000000010',
            designation='School Operations Admin',
            permissions='admissions,fees,students,attendance,website',
        ))

    staff_specs = [
        ('TEST_EMPLOYEE1_USERNAME', 'admission01', 'TEST_EMPLOYEE1_PASSWORD', 'admission@123', 'Admission Executive', 'admissions,students'),
        ('TEST_EMPLOYEE2_USERNAME', 'fees01', 'TEST_EMPLOYEE2_PASSWORD', 'fees@123', 'Fee Desk Executive', 'fees'),
        ('TEST_EMPLOYEE3_USERNAME', 'office01', 'TEST_EMPLOYEE3_PASSWORD', 'office@123', 'Office Executive', 'admissions,fees,messages'),
    ]
    for user_key, username_default, pass_key, password_default, designation, permissions in staff_specs:
        user = _user(_env(user_key, username_default), _env(pass_key, password_default), 'staff')
        if not user.staff_profile:
            db.session.add(StaffProfile(
                user_id=user.id,
                employee_code=user.username,
                full_name=designation,
                phone='90000000' + str(user.id).zfill(2)[-2:],
                designation=designation,
                permissions=permissions,
            ))

    teacher_user = _user(_env('TEST_TEACHER_USERNAME', 'teacher01'), _env('TEST_TEACHER_PASSWORD', 'teacher@123'), 'teacher')
    if not teacher_user.teacher_profile:
        db.session.add(TeacherProfile(
            user_id=teacher_user.id,
            employee_code=teacher_user.username,
            full_name='Demo Teacher',
            phone='9000000006',
            subject='Mathematics',
            assigned_classes='1,2,3',
            is_class_teacher=True,
        ))

    driver_user = _user(_env('TEST_DRIVER_USERNAME', 'driver01'), _env('TEST_DRIVER_PASSWORD', 'driver@123'), 'driver')
    if not driver_user.driver_profile:
        db.session.add(DriverProfile(
            user_id=driver_user.id,
            route_id=route.id,
            driver_name='Demo Driver',
            phone='9000000004',
            license_no='DL-DEMO-001',
            vehicle_no=route.vehicle_no,
        ))

    parent_user = _user(_env('TEST_PARENT_USERNAME', 'parent01'), _env('TEST_PARENT_PASSWORD', 'parent@123'), 'parent')
    parent = parent_user.parent_profile
    if not parent:
        parent = ParentProfile(
            user_id=parent_user.id,
            father_name='Demo Father',
            mother_name='Demo Mother',
            primary_phone='9000000001',
            address='Demo Address, Chandauli',
        )
        db.session.add(parent)
        db.session.flush()

    student_user = _user(_env('TEST_STUDENT_USERNAME', 'student01'), _env('TEST_STUDENT_PASSWORD', 'student@123'), 'student')
    student = student_user.student_profile
    if not student:
        student = StudentProfile(
            user_id=student_user.id,
            parent_id=parent.id,
            admission_no=student_user.username,
            full_name='Demo Student',
            dob=date(2018, 1, 1),
            gender='Male',
            current_class='1',
            section='A',
            roll_no='1',
        )
        db.session.add(student)
        db.session.flush()
        db.session.add(AcademicResult(
            student_id=student.id,
            term='Term 1 - 2026',
            subject_marks='{"Math": 88, "English": 84, "Science": 91}',
            total_marks=263,
            percentage=87.67,
            grade='A',
            remarks='Consistent progress.',
            is_published=True,
        ))

    if student and not student.transport_assignment:
        db.session.add(StudentTransport(
            student_id=student.id,
            route_id=route.id,
            pickup_point='Demo Pickup Point',
            drop_point='Demo Pickup Point',
        ))

    db.session.commit()
