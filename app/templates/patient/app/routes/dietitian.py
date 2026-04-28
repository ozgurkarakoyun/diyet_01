import secrets
from datetime import datetime, date, timedelta
from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, abort
from flask_login import login_required, current_user
from app import db, csrf
from app.models import (User, Dietitian, Patient, DietStage, PatientStageHistory,
                        Measurement, Supplement, Message, RegistrationCode)
from app.forms import (MessageForm, SupplementForm, RegistrationCodeForm,
                       StageChangeForm, PatientProfileForm)

dietitian_bp = Blueprint('dietitian', __name__)


def get_current_dietitian():
    if not current_user.is_authenticated or not current_user.is_dietitian():
        abort(403)
    return current_user.dietitian


def get_patient_or_404(patient_id, dietitian):
    patient = Patient.query.filter_by(id=patient_id, dietitian_id=dietitian.id).first_or_404()
    return patient


@dietitian_bp.route('/dashboard')
@login_required
def dashboard():
    dietitian = get_current_dietitian()
    patients = Patient.query.filter_by(dietitian_id=dietitian.id).order_by(Patient.created_at.desc()).all()
    
    active_count = sum(1 for p in patients if p.is_active)
    
    # Unread messages count
    unread_count = Message.query.filter_by(
        receiver_dietitian_id=dietitian.id,
        is_read=False
    ).count()

    # Check and auto-advance stages
    for patient in patients:
        if patient.is_active and patient.should_advance_stage():
            _auto_advance_stage(patient)
    db.session.commit()

    return render_template('dietitian/dashboard.html',
                           dietitian=dietitian,
                           patients=patients,
                           active_count=active_count,
                           unread_count=unread_count)


@dietitian_bp.route('/patient/<int:patient_id>')
@login_required
def patient_detail(patient_id):
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)
    stages = DietStage.query.order_by(DietStage.order).all()
    measurements = patient.measurements.order_by(Measurement.date.asc()).all()
    supplements = patient.supplements.order_by(Supplement.created_at.desc()).all()
    stage_history = patient.stage_history.order_by(PatientStageHistory.start_date.desc()).limit(20).all()

    # Messages
    messages = _get_conversation(patient.id, dietitian.id)
    _mark_patient_messages_read(patient.id, dietitian.id)

    message_form = MessageForm()
    stage_form = StageChangeForm()
    stage_form.stage_id.choices = [(s.id, f'{s.stage_number}. Etap – {s.name}') for s in stages]

    return render_template('dietitian/patient_detail.html',
                           patient=patient,
                           dietitian=dietitian,
                           stages=stages,
                           measurements=measurements,
                           supplements=supplements,
                           stage_history=stage_history,
                           messages=messages,
                           message_form=message_form,
                           stage_form=stage_form)


@dietitian_bp.route('/patient/<int:patient_id>/measurements')
@login_required
def patient_measurements(patient_id):
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)
    measurements = patient.measurements.order_by(Measurement.date.asc()).all()
    return render_template('dietitian/measurements.html',
                           patient=patient,
                           measurements=measurements)


@dietitian_bp.route('/patient/<int:patient_id>/change-stage', methods=['POST'])
@login_required
def change_stage(patient_id):
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)
    stages = DietStage.query.order_by(DietStage.order).all()

    form = StageChangeForm()
    form.stage_id.choices = [(s.id, f'{s.stage_number}. Etap') for s in stages]

    if form.validate_on_submit():
        new_stage = DietStage.query.get_or_404(form.stage_id.data)
        _change_patient_stage(patient, new_stage, changed_by='dietitian', notes=form.notes.data)
        db.session.commit()
        flash(f'{patient.nickname} için etap {new_stage.stage_number}. Etap olarak değiştirildi.', 'success')
    else:
        flash('Form hatası. Lütfen tekrar deneyin.', 'danger')

    return redirect(url_for('dietitian.patient_detail', patient_id=patient_id))


@dietitian_bp.route('/patient/<int:patient_id>/send-message', methods=['POST'])
@login_required
def send_message(patient_id):
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)

    form = MessageForm()
    if form.validate_on_submit():
        msg = Message(
            content=form.content.data.strip(),
            sender_type='dietitian',
            sender_dietitian_id=dietitian.id,
            receiver_patient_id=patient.id
        )
        db.session.add(msg)
        db.session.commit()
        flash('Mesaj gönderildi.', 'success')
    else:
        flash('Mesaj boş olamaz.', 'danger')

    return redirect(url_for('dietitian.patient_detail', patient_id=patient_id))


@dietitian_bp.route('/patient/<int:patient_id>/supplements', methods=['GET', 'POST'])
@login_required
def manage_supplements(patient_id):
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)
    form = SupplementForm()

    if form.validate_on_submit():
        supplement = Supplement(
            patient_id=patient.id,
            dietitian_id=dietitian.id,
            product_name=form.product_name.data.strip(),
            description=form.description.data,
            usage_instructions=form.usage_instructions.data,
            usage_time=form.usage_time.data,
            start_date=form.start_date.data,
            end_date=form.end_date.data,
            is_active=form.is_active.data
        )
        db.session.add(supplement)
        db.session.commit()
        flash('Takviye/ek gıda eklendi.', 'success')
        return redirect(url_for('dietitian.patient_detail', patient_id=patient_id))

    supplements = patient.supplements.order_by(Supplement.created_at.desc()).all()
    return render_template('dietitian/supplements.html',
                           patient=patient,
                           form=form,
                           supplements=supplements)


@dietitian_bp.route('/supplement/<int:supplement_id>/toggle', methods=['POST'])
@login_required
def toggle_supplement(supplement_id):
    dietitian = get_current_dietitian()
    supplement = Supplement.query.filter_by(id=supplement_id, dietitian_id=dietitian.id).first_or_404()
    supplement.is_active = not supplement.is_active
    db.session.commit()
    flash('Takviye durumu güncellendi.', 'success')
    return redirect(url_for('dietitian.patient_detail', patient_id=supplement.patient_id))


@dietitian_bp.route('/supplement/<int:supplement_id>/delete', methods=['POST'])
@login_required
def delete_supplement(supplement_id):
    dietitian = get_current_dietitian()
    supplement = Supplement.query.filter_by(id=supplement_id, dietitian_id=dietitian.id).first_or_404()
    patient_id = supplement.patient_id
    db.session.delete(supplement)
    db.session.commit()
    flash('Takviye silindi.', 'info')
    return redirect(url_for('dietitian.patient_detail', patient_id=patient_id))


@dietitian_bp.route('/codes')
@login_required
def registration_codes():
    dietitian = get_current_dietitian()
    form = RegistrationCodeForm()
    codes = RegistrationCode.query.filter_by(dietitian_id=dietitian.id).order_by(
        RegistrationCode.created_at.desc()).all()
    return render_template('dietitian/codes.html', form=form, codes=codes, dietitian=dietitian)


@dietitian_bp.route('/codes/create', methods=['POST'])
@login_required
def create_code():
    dietitian = get_current_dietitian()
    form = RegistrationCodeForm()

    if form.validate_on_submit():
        expires_at = None
        if form.expires_days.data and form.expires_days.data > 0:
            expires_at = datetime.utcnow() + timedelta(days=form.expires_days.data)

        code = RegistrationCode(
            code=form.code.data.strip().upper(),
            dietitian_id=dietitian.id,
            expires_at=expires_at
        )
        db.session.add(code)
        db.session.commit()
        flash(f'Kayıt kodu oluşturuldu: {code.code}', 'success')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')

    return redirect(url_for('dietitian.registration_codes'))


@dietitian_bp.route('/codes/generate', methods=['POST'])
@login_required
def generate_code():
    dietitian = get_current_dietitian()
    code_str = secrets.token_urlsafe(6).upper()
    expires_at = datetime.utcnow() + timedelta(days=30)

    code = RegistrationCode(
        code=code_str,
        dietitian_id=dietitian.id,
        expires_at=expires_at
    )
    db.session.add(code)
    db.session.commit()
    flash(f'Otomatik kod oluşturuldu: {code.code} (30 gün geçerli)', 'success')
    return redirect(url_for('dietitian.registration_codes'))


@dietitian_bp.route('/codes/<int:code_id>/delete', methods=['POST'])
@login_required
def delete_code(code_id):
    dietitian = get_current_dietitian()
    code = RegistrationCode.query.filter_by(id=code_id, dietitian_id=dietitian.id).first_or_404()
    if code.is_used:
        flash('Kullanılmış kod silinemez.', 'warning')
    else:
        db.session.delete(code)
        db.session.commit()
        flash('Kod silindi.', 'info')
    return redirect(url_for('dietitian.registration_codes'))


@dietitian_bp.route('/patient/<int:patient_id>/toggle-active', methods=['POST'])
@login_required
def toggle_patient_active(patient_id):
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)
    patient.is_active = not patient.is_active
    patient.user.is_active = patient.is_active
    db.session.commit()
    status = 'aktif' if patient.is_active else 'pasif'
    flash(f'{patient.nickname} {status} yapıldı.', 'success')
    return redirect(url_for('dietitian.dashboard'))


# ── Helpers ──────────────────────────────────────────────────────────────────

def _get_conversation(patient_id, dietitian_id):
    sent = Message.query.filter_by(sender_dietitian_id=dietitian_id, receiver_patient_id=patient_id)
    received = Message.query.filter_by(sender_patient_id=patient_id, receiver_dietitian_id=dietitian_id)
    all_msgs = sent.union(received).order_by(Message.created_at.asc()).all()
    return all_msgs


def _mark_patient_messages_read(patient_id, dietitian_id):
    msgs = Message.query.filter_by(
        sender_patient_id=patient_id,
        receiver_dietitian_id=dietitian_id,
        is_read=False
    ).all()
    for msg in msgs:
        msg.mark_as_read()


def _change_patient_stage(patient, new_stage, changed_by='auto', notes=None):
    today = date.today()

    # Close current stage history
    current_history = PatientStageHistory.query.filter_by(
        patient_id=patient.id,
        end_date=None
    ).first()
    if current_history:
        current_history.end_date = today

    # Determine cycle number
    cycle = patient.cycle_number or 1
    if new_stage.stage_number == 1 and changed_by == 'auto':
        cycle += 1
        patient.cycle_number = cycle

    patient.current_stage_id = new_stage.id
    patient.stage_start_date = today
    patient.is_free_day = new_stage.is_free_day

    new_history = PatientStageHistory(
        patient_id=patient.id,
        stage_id=new_stage.id,
        start_date=today,
        cycle_number=cycle,
        changed_by=changed_by,
        notes=notes
    )
    db.session.add(new_history)


@dietitian_bp.route('/patient/<int:patient_id>/ai-assist', methods=['POST'])
@csrf.exempt
def ai_assist(patient_id):
    """Hasta verileri üzerinden AI yardımı — Anthropic API çağrısı."""
    import os, requests as req
    if not current_user.is_authenticated:
        return jsonify({'error': 'Oturum açık değil.'}), 401
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)

    data = request.get_json(force=True, silent=True)
    user_question = (data or {}).get('question', '').strip()
    if not user_question:
        return jsonify({'error': 'Soru boş olamaz.'}), 400
    last_m = patient.get_last_measurement()
    bmi_str = ''
    if last_m and last_m.weight and patient.height_cm:
        bmi = round(last_m.weight / ((patient.height_cm / 100) ** 2), 1)
        bmi_str = f', BKİ={bmi}'

    stage_name = patient.current_stage.name if patient.current_stage else 'Etap atanmamış'
    stage_day  = patient.get_days_in_current_stage()

    patient_summary = (
        f"Hasta: {patient.nickname}, "
        f"Cinsiyet: {'Kadın' if patient.gender=='female' else 'Erkek' if patient.gender=='male' else '?'}, "
        f"Boy: {patient.height_cm or '?'} cm, "
        f"Başlangıç kilosu: {patient.start_weight or '?'} kg"
        f"{bmi_str}, "
        f"Aktif etap: {stage_name} ({stage_day}. gün), "
        f"Döngü: {patient.cycle_number}"
    )
    if last_m:
        patient_summary += (
            f"\nSon ölçüm ({last_m.date}): "
            f"kilo={last_m.weight}, göbek={last_m.gobek}, "
            f"bel={last_m.bel}, kalça={last_m.kalca}"
        )
    if patient.notes:
        patient_summary += f"\nHasta notları: {patient.notes}"

    system_prompt = """Sen deneyimli bir diyetisyenin asistanısın. 
Aşağıdaki diyet programı kurallarına hakimsin:

PROGRAM KURALLARI:
- 1.Etap (4 gün): Saf protein - tavuk, hindi, balık, kırmızı et, yumurta, mantar. Sabah yoğurt+vitalif yulaf ezmesi, öğle/akşam küçük kase yoğurt + unsuz çorba.
- 2.Etap (5 gün): 1.etap + çiğ sebzeler (roka,tere,nane,maydanoz,salatalık,turp,biber,semizotu,kereviz,yeşil soğan,kıvırcık,marul,az domates,avokado,mor/beyaz lahana). Havuç ve dereotu yasak.
- 3.Etap (5 gün): 1+2.etap + kahvaltıya peynir/zeytin/3ceviz/7badem + öğle/akşama pişmiş sebze (kabak,patlıcan,biber,yeşil fasulye,bamya,enginar). %40 et %30 salata %30 tencere. Öğle/akşam unsuz sebze veya mercimek çorbası (sırayla).
- 4.Etap (7 gün): 4 çalma + 3 saf protein, dönüşümlü. Çalma kahvaltı: 3 kuru kayısı + yulaf ezmeli yoğurt + küçük meyve + ince ekmek + yumurta/pastırma/sucuk/zeytin/peynir.
- Serbest Gün (1 gün): 21 günlük programın sonunda. Abartma, her şeyden az az.
- Genel: Öğünler arası en az 4 saat, her 25 kg için 1 litre su, sakız yasak.
- Kilo verme durursa: Maydanoz-limon karışımı sabah aç karnına, gün aşırı (1.etap dışında). Probiyotik yoğurt karışımı akşam öğünü (zencefil, zerdeçal, keten tohumu, tarçın, yulaf kepeği/ezmesi, kayısı, ceviz) — haftada max 2 kez.
- Kabızlık: Gece 2 kayısı + 2 ceviz suda beklet, sabah aç karnına iç. Activize'dan 5 dk sonra tüket. Gece magnezyum.

Kısa, net, pratik yanıtlar ver. Türkçe yaz. Başka hastalara veya kaynaklara referans verme. 
Yalnızca bu program çerçevesinde önerilerde bulun."""

    try:
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        resp = req.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 1024,
                'system': system_prompt,
                'messages': [
                    {'role': 'user', 'content': f"Hasta bilgileri:\n{patient_summary}\n\nSorum: {user_question}"}
                ]
            },
            timeout=30
        )
        resp.raise_for_status()
        answer = resp.json()['content'][0]['text']
        return jsonify({'answer': answer})
    except Exception as e:
        return jsonify({'error': f'AI yanıt alınamadı: {str(e)}'}), 500


@dietitian_bp.route('/patient/<int:patient_id>/update-notes', methods=['POST'])
@csrf.exempt
def update_patient_notes(patient_id):
    """Hasta iç notları ve kişisel programı güncelle."""
    if not current_user.is_authenticated:
        return jsonify({'error': 'Oturum açık değil.'}), 401
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)
    data = request.get_json(force=True, silent=True)
    if 'notes' in (data or {}):
        patient.notes = data.get('notes', '').strip()
    if 'personal_program' in (data or {}):
        patient.personal_program = data.get('personal_program', '').strip()
    db.session.commit()
    return jsonify({'ok': True})


@dietitian_bp.route('/patient/<int:patient_id>/ai-generate-program', methods=['POST'])
@csrf.exempt
def ai_generate_program(patient_id):
    """AI ile kişisel program taslağı oluştur."""
    import os, requests as req
    if not current_user.is_authenticated:
        return jsonify({'error': 'Oturum açık değil.'}), 401
    dietitian = get_current_dietitian()
    patient = get_patient_or_404(patient_id, dietitian)

    data = request.get_json(force=True, silent=True)
    instructions = (data or {}).get('instructions', '').strip()

    last_m = patient.get_last_measurement()
    bmi_str = ''
    if last_m and last_m.weight and patient.height_cm:
        bmi = round(last_m.weight / ((patient.height_cm / 100) ** 2), 1)
        bmi_str = f', BKİ={bmi}'

    stage_name = patient.current_stage.name if patient.current_stage else 'Etap atanmamış'

    patient_summary = (
        f"Hasta: {patient.nickname}, "
        f"Cinsiyet: {'Kadın' if patient.gender=='female' else 'Erkek' if patient.gender=='male' else '?'}, "
        f"Boy: {patient.height_cm or '?'} cm{bmi_str}, "
        f"Aktif etap: {stage_name} ({patient.get_days_in_current_stage()}. gün), "
        f"Döngü: {patient.cycle_number}"
    )
    if last_m:
        patient_summary += (
            f"\nSon ölçüm ({last_m.date}): kilo={last_m.weight}, "
            f"göbek={last_m.gobek}, bel={last_m.bel}, kalça={last_m.kalca}"
        )
    if patient.notes:
        patient_summary += f"\nDiyetisyen notları: {patient.notes}"
    if patient.personal_program:
        patient_summary += f"\nMevcut kişisel program:\n{patient.personal_program}"

    system_prompt = """Sen deneyimli bir diyetisyenin asistanısın. Hastaya özel, kişiselleştirilmiş diyet programı metni yazıyorsun.

Bu metin doğrudan HASTAYA gösterilecek — nazik, teşvik edici ve anlaşılır yaz.
Teknik jargon kullanma. Madde madde, net ve uygulanabilir yaz.

Program şu başlıkları içermeli (gerekli olanları):
- 🎯 Senin İçin Özel Notlar
- ✅ Yiyebileceklerin (etabına göre)
- 🚫 Dikkat Etmen Gerekenler  
- 💊 Takviye / Protokol (varsa)
- 💪 Motivasyon

Sadece hastanın mevcut etabıyla ilgili bilgileri yaz. Diğer etapları detaylandırma.
Türkçe yaz. Maksimum 400 kelime."""

    try:
        api_key = os.getenv('ANTHROPIC_API_KEY', '')
        prompt = f"Hasta bilgileri:\n{patient_summary}\n\nDiyetisyen talimatları: {instructions if instructions else 'Standart kişisel program oluştur.'}"
        resp = req.post(
            'https://api.anthropic.com/v1/messages',
            headers={
                'x-api-key': api_key,
                'anthropic-version': '2023-06-01',
                'content-type': 'application/json'
            },
            json={
                'model': 'claude-haiku-4-5-20251001',
                'max_tokens': 1024,
                'system': system_prompt,
                'messages': [{'role': 'user', 'content': prompt}]
            },
            timeout=30
        )
        resp.raise_for_status()
        program_text = resp.json()['content'][0]['text']
        return jsonify({'program': program_text})
    except Exception as e:
        return jsonify({'error': f'AI yanıt alınamadı: {str(e)}'}), 500


def _auto_advance_stage(patient):
    if not patient.current_stage:
        return

    stages = DietStage.query.order_by(DietStage.order).all()
    stage_map = {s.id: i for i, s in enumerate(stages)}
    current_idx = stage_map.get(patient.current_stage_id)

    if current_idx is None:
        return

    # If current is free day → go to stage 1
    if patient.current_stage.is_free_day:
        stage1 = DietStage.query.filter_by(stage_number=1).first()
        if stage1:
            _change_patient_stage(patient, stage1, changed_by='auto')
        return

    next_idx = current_idx + 1
    if next_idx < len(stages):
        next_stage = stages[next_idx]
        _change_patient_stage(patient, next_stage, changed_by='auto')
    else:
        # After last stage → free day (if exists) or back to stage 1
        free_day = DietStage.query.filter_by(is_free_day=True).first()
        if free_day:
            _change_patient_stage(patient, free_day, changed_by='auto')
        else:
            stage1 = DietStage.query.filter_by(stage_number=1).first()
            if stage1:
                _change_patient_stage(patient, stage1, changed_by='auto')
