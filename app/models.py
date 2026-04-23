from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db, login_manager


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'dietitian' or 'patient'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dietitian = db.relationship('Dietitian', backref='user', uselist=False, cascade='all, delete-orphan')
    patient = db.relationship('Patient', backref='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_dietitian(self):
        return self.role == 'dietitian'

    def is_patient(self):
        return self.role == 'patient'

    def __repr__(self):
        return f'<User {self.email}>'


class Dietitian(db.Model):
    __tablename__ = 'dietitians'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    bio = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patients = db.relationship('Patient', backref='dietitian', lazy='dynamic')
    registration_codes = db.relationship('RegistrationCode', backref='dietitian', lazy='dynamic')

    def __repr__(self):
        return f'<Dietitian {self.name}>'


class RegistrationCode(db.Model):
    __tablename__ = 'registration_codes'

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(50), unique=True, nullable=False, index=True)
    dietitian_id = db.Column(db.Integer, db.ForeignKey('dietitians.id'), nullable=False)
    is_used = db.Column(db.Boolean, default=False)
    used_by_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def is_valid(self):
        if self.is_used:
            return False
        if self.expires_at and self.expires_at < datetime.utcnow():
            return False
        return True

    def __repr__(self):
        return f'<RegistrationCode {self.code}>'


class DietStage(db.Model):
    __tablename__ = 'diet_stages'

    id = db.Column(db.Integer, primary_key=True)
    stage_number = db.Column(db.Integer, nullable=False)  # 1, 2, 3, 4
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    duration_days = db.Column(db.Integer, nullable=False)
    allowed_foods = db.Column(db.Text)  # JSON string
    rules = db.Column(db.Text)
    is_free_day = db.Column(db.Boolean, default=False)
    order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    patient_stages = db.relationship('PatientStageHistory', backref='stage', lazy='dynamic')

    def __repr__(self):
        return f'<DietStage {self.stage_number}: {self.name}>'


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dietitian_id = db.Column(db.Integer, db.ForeignKey('dietitians.id'), nullable=False)
    nickname = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    birth_date = db.Column(db.Date)
    gender = db.Column(db.String(10))
    height_cm = db.Column(db.Float)
    start_weight = db.Column(db.Float)
    notes = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)

    # Current stage tracking
    current_stage_id = db.Column(db.Integer, db.ForeignKey('diet_stages.id'), nullable=True)
    stage_start_date = db.Column(db.Date, nullable=True)
    is_free_day = db.Column(db.Boolean, default=False)
    free_day_date = db.Column(db.Date, nullable=True)
    cycle_number = db.Column(db.Integer, default=1)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    current_stage = db.relationship('DietStage', foreign_keys=[current_stage_id])
    stage_history = db.relationship('PatientStageHistory', backref='patient', lazy='dynamic',
                                    foreign_keys='PatientStageHistory.patient_id')
    measurements = db.relationship('Measurement', backref='patient', lazy='dynamic')
    supplements = db.relationship('Supplement', backref='patient', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys='Message.sender_patient_id',
                                    backref='sender_patient', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys='Message.receiver_patient_id',
                                        backref='receiver_patient', lazy='dynamic')
    used_code = db.relationship('RegistrationCode', foreign_keys='RegistrationCode.used_by_patient_id',
                                backref='used_by', uselist=False)

    def get_last_measurement(self):
        return self.measurements.order_by(Measurement.date.desc()).first()

    def get_days_in_current_stage(self):
        if self.stage_start_date:
            return (date.today() - self.stage_start_date).days + 1
        return 0

    def should_advance_stage(self):
        if not self.current_stage or not self.stage_start_date:
            return False
        days_in_stage = self.get_days_in_current_stage()
        if self.current_stage.is_free_day:
            return days_in_stage >= 1
        return days_in_stage > self.current_stage.duration_days

    def __repr__(self):
        return f'<Patient {self.nickname}>'


class PatientStageHistory(db.Model):
    __tablename__ = 'patient_stage_history'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    stage_id = db.Column(db.Integer, db.ForeignKey('diet_stages.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=True)
    cycle_number = db.Column(db.Integer, default=1)
    changed_by = db.Column(db.String(20), default='auto')  # 'auto' or 'dietitian'
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<PatientStageHistory patient={self.patient_id} stage={self.stage_id}>'


class Measurement(db.Model):
    __tablename__ = 'measurements'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)

    # Body measurements in cm
    boyun = db.Column(db.Float)           # Boyun çevresi
    ust_gogus = db.Column(db.Float)       # Üst göğüs
    gogus = db.Column(db.Float)           # Göğüs
    alt_gogus = db.Column(db.Float)       # Alt göğüs
    gobek = db.Column(db.Float)           # Göbek
    bel = db.Column(db.Float)             # Bel
    kalca = db.Column(db.Float)           # Kalça
    sag_kol = db.Column(db.Float)         # Sağ kol kalınlığı
    sol_kol = db.Column(db.Float)         # Sol kol kalınlığı
    sag_bacak = db.Column(db.Float)       # Sağ bacak kalınlığı
    sol_bacak = db.Column(db.Float)       # Sol bacak kalınlığı
    weight = db.Column(db.Float)          # Kilo (opsiyonel)

    notes = db.Column(db.Text)
    stage_id = db.Column(db.Integer, db.ForeignKey('diet_stages.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    stage = db.relationship('DietStage', foreign_keys=[stage_id])

    def total_cm(self):
        fields = [self.boyun, self.ust_gogus, self.gogus, self.alt_gogus,
                  self.gobek, self.bel, self.kalca,
                  self.sag_kol, self.sol_kol, self.sag_bacak, self.sol_bacak]
        return sum(f for f in fields if f is not None)

    def __repr__(self):
        return f'<Measurement patient={self.patient_id} date={self.date}>'


class Supplement(db.Model):
    __tablename__ = 'supplements'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    dietitian_id = db.Column(db.Integer, db.ForeignKey('dietitians.id'), nullable=False)
    product_name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    usage_instructions = db.Column(db.Text)
    usage_time = db.Column(db.String(100))  # sabah, akşam, yemekten önce, vb.
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    dietitian = db.relationship('Dietitian', foreign_keys=[dietitian_id])

    def __repr__(self):
        return f'<Supplement {self.product_name}>'


class Message(db.Model):
    __tablename__ = 'messages'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'dietitian' or 'patient'

    # Dietitian side
    sender_dietitian_id = db.Column(db.Integer, db.ForeignKey('dietitians.id'), nullable=True)
    receiver_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)

    # Patient side
    sender_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    receiver_dietitian_id = db.Column(db.Integer, db.ForeignKey('dietitians.id'), nullable=True)

    is_read = db.Column(db.Boolean, default=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sender_dietitian = db.relationship('Dietitian', foreign_keys=[sender_dietitian_id],
                                       backref='sent_messages')
    receiver_dietitian = db.relationship('Dietitian', foreign_keys=[receiver_dietitian_id],
                                         backref='received_messages')

    def mark_as_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()

    def __repr__(self):
        return f'<Message from={self.sender_type} id={self.id}>'
