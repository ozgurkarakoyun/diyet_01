from datetime import date
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db
from app.models import (Patient, Measurement, Message, Supplement,
                        DietStage, PatientStageHistory)
from app.forms import MeasurementForm, MessageForm, PatientProfileForm

patient_bp = Blueprint('patient', __name__)


def get_current_patient():
    if not current_user.is_authenticated or not current_user.is_patient():
        abort(403)
    return current_user.patient


@patient_bp.route('/dashboard')
@login_required
def dashboard():
    patient = get_current_patient()
    last_measurement = patient.get_last_measurement()
    active_supplements = patient.supplements.filter_by(is_active=True).all()

    # Unread messages from dietitian
    unread_count = Message.query.filter_by(
        receiver_patient_id=patient.id,
        is_read=False
    ).count()

    # Days remaining in stage
    days_in_stage = patient.get_days_in_current_stage()
    days_remaining = 0
    if patient.current_stage and not patient.current_stage.is_free_day:
        days_remaining = max(0, patient.current_stage.duration_days - days_in_stage + 1)

    return render_template('patient/dashboard.html',
                           patient=patient,
                           last_measurement=last_measurement,
                           active_supplements=active_supplements,
                           unread_count=unread_count,
                           days_in_stage=days_in_stage,
                           days_remaining=days_remaining)


@patient_bp.route('/measurements', methods=['GET', 'POST'])
@login_required
def measurements():
    patient = get_current_patient()
    form = MeasurementForm()

    if form.validate_on_submit():
        measurement = Measurement(
            patient_id=patient.id,
            date=form.date.data,
            boyun=form.boyun.data,
            ust_gogus=form.ust_gogus.data,
            gogus=form.gogus.data,
            alt_gogus=form.alt_gogus.data,
            gobek=form.gobek.data,
            bel=form.bel.data,
            kalca=form.kalca.data,
            sag_kol=form.sag_kol.data,
            sol_kol=form.sol_kol.data,
            sag_bacak=form.sag_bacak.data,
            sol_bacak=form.sol_bacak.data,
            weight=form.weight.data,
            notes=form.notes.data,
            stage_id=patient.current_stage_id
        )
        db.session.add(measurement)
        db.session.commit()
        flash('Ölçümünüz kaydedildi!', 'success')
        return redirect(url_for('patient.measurements'))

    # Default date to today
    if request.method == 'GET':
        form.date.data = date.today()

    all_measurements = patient.measurements.order_by(Measurement.date.desc()).all()
    return render_template('patient/measurements.html',
                           patient=patient,
                           form=form,
                           measurements=all_measurements)


@patient_bp.route('/measurements/data')
@login_required
def measurements_data():
    """API endpoint for chart data"""
    patient = get_current_patient()
    measurements = patient.measurements.order_by(Measurement.date.asc()).all()

    data = {
        'labels': [m.date.strftime('%d.%m.%Y') for m in measurements],
        'boyun': [m.boyun for m in measurements],
        'gobek': [m.gobek for m in measurements],
        'bel': [m.bel for m in measurements],
        'kalca': [m.kalca for m in measurements],
        'weight': [m.weight for m in measurements],
        'total': [m.total_cm() for m in measurements],
    }
    return jsonify(data)


@patient_bp.route('/messages', methods=['GET', 'POST'])
@login_required
def messages():
    patient = get_current_patient()
    form = MessageForm()

    if form.validate_on_submit():
        msg = Message(
            content=form.content.data.strip(),
            sender_type='patient',
            sender_patient_id=patient.id,
            receiver_dietitian_id=patient.dietitian_id
        )
        db.session.add(msg)
        db.session.commit()
        flash('Mesajınız gönderildi.', 'success')
        return redirect(url_for('patient.messages'))

    # Get conversation
    sent = Message.query.filter_by(sender_patient_id=patient.id,
                                   receiver_dietitian_id=patient.dietitian_id)
    received = Message.query.filter_by(sender_dietitian_id=patient.dietitian_id,
                                       receiver_patient_id=patient.id)
    all_messages = sent.union(received).order_by(Message.created_at.asc()).all()

    # Mark dietitian messages as read
    unread = Message.query.filter_by(
        sender_dietitian_id=patient.dietitian_id,
        receiver_patient_id=patient.id,
        is_read=False
    ).all()
    for msg in unread:
        msg.mark_as_read()
    db.session.commit()

    return render_template('patient/messages.html',
                           patient=patient,
                           messages=all_messages,
                           form=form)


@patient_bp.route('/supplements')
@login_required
def supplements():
    patient = get_current_patient()
    active = patient.supplements.filter_by(is_active=True).order_by(Supplement.created_at.desc()).all()
    inactive = patient.supplements.filter_by(is_active=False).order_by(Supplement.created_at.desc()).all()
    return render_template('patient/supplements.html',
                           patient=patient,
                           active_supplements=active,
                           inactive_supplements=inactive)


@patient_bp.route('/diet-rules')
@login_required
def diet_rules():
    patient = get_current_patient()
    stages = DietStage.query.order_by(DietStage.order).all()
    return render_template('patient/diet_rules.html',
                           patient=patient,
                           stages=stages)


@patient_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    patient = get_current_patient()
    form = PatientProfileForm(obj=patient)

    if form.validate_on_submit():
        patient.nickname = form.nickname.data.strip()
        patient.phone = form.phone.data
        patient.gender = form.gender.data
        patient.height_cm = form.height_cm.data
        patient.start_weight = form.start_weight.data
        db.session.commit()
        flash('Profiliniz güncellendi.', 'success')
        return redirect(url_for('patient.profile'))

    return render_template('patient/profile.html', patient=patient, form=form)
