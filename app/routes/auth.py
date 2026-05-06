from datetime import datetime, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request
from urllib.parse import urlparse, urljoin
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from app.models import User, Dietitian, Patient, RegistrationCode, DietStage, PatientStageHistory
from app.forms import LoginForm, PatientRegisterForm, DietitianRegisterForm
import os

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data.lower().strip()).first()
        if user and user.check_password(form.password.data):
            if not user.is_active:
                flash('Hesabınız devre dışı. Lütfen diyetisyeninizle iletişime geçin.', 'danger')
                return render_template('auth/login.html', form=form)
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if _is_safe_url(next_page):
                return redirect(next_page)
            return _redirect_by_role(user)
        flash('E-posta veya şifre hatalı.', 'danger')
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Başarıyla çıkış yaptınız.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register/patient', methods=['GET', 'POST'])
def register_patient():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = PatientRegisterForm()
    if form.validate_on_submit():
        code_obj = RegistrationCode.query.filter_by(code=form.registration_code.data).first()

        user = User(
            email=form.email.data.lower().strip(),
            role='patient'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        # Get first stage
        first_stage = DietStage.query.filter_by(stage_number=1).first()

        patient = Patient(
            user_id=user.id,
            dietitian_id=code_obj.dietitian_id,
            nickname=form.nickname.data.strip(),
            current_stage_id=first_stage.id if first_stage else None,
            stage_start_date=datetime.utcnow().date(),
            cycle_number=1
        )
        db.session.add(patient)
        db.session.flush()

        # Mark code as used
        code_obj.is_used = True
        code_obj.used_by_patient_id = patient.id

        # Stage history
        if first_stage:
            history = PatientStageHistory(
                patient_id=patient.id,
                stage_id=first_stage.id,
                start_date=datetime.utcnow().date(),
                cycle_number=1,
                changed_by='auto'
            )
            db.session.add(history)

        db.session.commit()
        flash('Kayıt başarılı! Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_patient.html', form=form)


@auth_bp.route('/register/dietitian', methods=['GET', 'POST'])
def register_dietitian():
    if current_user.is_authenticated:
        return _redirect_by_role(current_user)

    form = DietitianRegisterForm()
    if form.validate_on_submit():
        admin_key = os.environ.get('DIETITIAN_ADMIN_KEY')
        if not admin_key:
            flash('Diyetisyen kaydı şu anda kapalı. Lütfen sistem yöneticisiyle iletişime geçin.', 'danger')
            return render_template('auth/register_dietitian.html', form=form)
        if form.admin_key.data != admin_key:
            flash('Geçersiz admin anahtarı.', 'danger')
            return render_template('auth/register_dietitian.html', form=form)

        user = User(
            email=form.email.data.lower().strip(),
            role='dietitian'
        )
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.flush()

        dietitian = Dietitian(
            user_id=user.id,
            name=form.name.data.strip()
        )
        db.session.add(dietitian)
        db.session.commit()
        flash('Diyetisyen hesabı oluşturuldu. Giriş yapabilirsiniz.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register_dietitian.html', form=form)


def _is_safe_url(target):
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def _redirect_by_role(user):
    if user.is_dietitian():
        return redirect(url_for('dietitian.dashboard'))
    elif user.is_patient():
        return redirect(url_for('patient.dashboard'))
    return redirect(url_for('main.index'))
