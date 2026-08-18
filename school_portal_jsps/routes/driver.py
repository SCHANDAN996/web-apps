from datetime import datetime

from flask import Blueprint, jsonify, redirect, render_template, request, session, url_for, flash

from decorators import driver_required
from extensions import db
from models import BusLocation, DriverProfile

driver_bp = Blueprint('driver', __name__, url_prefix='/driver')


def current_driver():
    return DriverProfile.query.filter_by(user_id=session.get('user_id')).first_or_404()


@driver_bp.route('/dashboard')
@driver_required
def dashboard():
    driver = current_driver()
    last_location = BusLocation.query.filter_by(driver_id=driver.id).order_by(BusLocation.recorded_at.desc()).first()
    return render_template('driver/dashboard.html', driver=driver, last_location=last_location)


@driver_bp.route('/location', methods=['POST'])
@driver_required
def update_location():
    driver = current_driver()
    latitude = request.form.get('latitude') or (request.get_json(silent=True) or {}).get('latitude')
    longitude = request.form.get('longitude') or (request.get_json(silent=True) or {}).get('longitude')
    if not latitude or not longitude:
        if request.is_json:
            return jsonify({'error': 'latitude and longitude are required'}), 400
        flash('Location not available. Please allow location permission.', 'error')
        return redirect(url_for('driver.dashboard'))

    location = BusLocation(
        driver_id=driver.id,
        route_id=driver.route_id,
        latitude=float(latitude),
        longitude=float(longitude),
        accuracy=float(request.form.get('accuracy') or (request.get_json(silent=True) or {}).get('accuracy') or 0),
        speed=float(request.form.get('speed') or (request.get_json(silent=True) or {}).get('speed') or 0),
        address_hint=request.form.get('address_hint') or (request.get_json(silent=True) or {}).get('address_hint') or '',
        recorded_at=datetime.utcnow(),
    )
    db.session.add(location)
    db.session.commit()
    if request.is_json:
        return jsonify({'success': True, 'recorded_at': location.recorded_at.strftime('%Y-%m-%d %H:%M:%S')}), 201
    flash('Bus location updated successfully.', 'success')
    return redirect(url_for('driver.dashboard'))
