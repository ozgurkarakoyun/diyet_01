from flask_wtf import FlaskForm
from wtforms import (StringField, PasswordField, SubmitField, TextAreaField,
                     SelectField, FloatField, DateField, BooleanField, IntegerField,
                     HiddenField)
from wtforms.validators import (DataRequired, Email, Length, EqualTo, Optional,
                                NumberRange, ValidationError)
from app.models import User, RegistrationCode


class LoginForm(FlaskForm):
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired()])
    remember_me = BooleanField('Beni Hatırla')
    submit = SubmitField('Giriş Yap')


class PatientRegisterForm(FlaskForm):
    nickname = StringField('Adınız veya Rumuzunuz', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=6)])
    password2 = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('password', message='Şifreler eşleşmiyor')])
    registration_code = StringField('Kayıt Kodu (Diyetisyeninizden alınız)', validators=[DataRequired()])
    submit = SubmitField('Kayıt Ol')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu e-posta adresi zaten kayıtlı.')

    def validate_registration_code(self, registration_code):
        code = RegistrationCode.query.filter_by(code=registration_code.data).first()
        if not code or not code.is_valid():
            raise ValidationError('Geçersiz veya kullanılmış kayıt kodu.')


class DietitianRegisterForm(FlaskForm):
    name = StringField('Ad Soyad', validators=[DataRequired(), Length(min=2, max=100)])
    email = StringField('E-posta', validators=[DataRequired(), Email()])
    password = PasswordField('Şifre', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Şifre Tekrar', validators=[DataRequired(), EqualTo('password')])
    admin_key = StringField('Admin Anahtarı', validators=[DataRequired()])
    submit = SubmitField('Diyetisyen Hesabı Oluştur')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Bu e-posta adresi zaten kayıtlı.')


class MeasurementForm(FlaskForm):
    date = DateField('Tarih', validators=[DataRequired()])
    boyun = FloatField('Boyun Çevresi (cm)', validators=[Optional(), NumberRange(min=1, max=200)])
    ust_gogus = FloatField('Üst Göğüs (cm)', validators=[Optional(), NumberRange(min=1, max=300)])
    gogus = FloatField('Göğüs (cm)', validators=[Optional(), NumberRange(min=1, max=300)])
    alt_gogus = FloatField('Alt Göğüs (cm)', validators=[Optional(), NumberRange(min=1, max=300)])
    gobek = FloatField('Göbek (cm)', validators=[Optional(), NumberRange(min=1, max=300)])
    bel = FloatField('Bel (cm)', validators=[Optional(), NumberRange(min=1, max=300)])
    kalca = FloatField('Kalça (cm)', validators=[Optional(), NumberRange(min=1, max=300)])
    sag_kol = FloatField('Sağ Kol (cm)', validators=[Optional(), NumberRange(min=1, max=100)])
    sol_kol = FloatField('Sol Kol (cm)', validators=[Optional(), NumberRange(min=1, max=100)])
    sag_bacak = FloatField('Sağ Bacak (cm)', validators=[Optional(), NumberRange(min=1, max=200)])
    sol_bacak = FloatField('Sol Bacak (cm)', validators=[Optional(), NumberRange(min=1, max=200)])
    weight = FloatField('Kilo (kg)', validators=[Optional(), NumberRange(min=20, max=500)])
    notes = TextAreaField('Notlar', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Ölçümü Kaydet')


class MessageForm(FlaskForm):
    content = TextAreaField('Mesajınız', validators=[DataRequired(), Length(min=1, max=2000)])
    submit = SubmitField('Gönder')


class SupplementForm(FlaskForm):
    product_name = StringField('Ürün Adı', validators=[DataRequired(), Length(max=200)])
    description = TextAreaField('Açıklama', validators=[Optional(), Length(max=1000)])
    usage_instructions = TextAreaField('Kullanım Şekli', validators=[Optional(), Length(max=500)])
    usage_time = StringField('Kullanım Zamanı', validators=[Optional(), Length(max=100)])
    start_date = DateField('Başlangıç Tarihi', validators=[Optional()])
    end_date = DateField('Bitiş Tarihi', validators=[Optional()])
    is_active = BooleanField('Aktif', default=True)
    submit = SubmitField('Kaydet')


class RegistrationCodeForm(FlaskForm):
    code = StringField('Kayıt Kodu', validators=[DataRequired(), Length(min=4, max=50)])
    expires_days = IntegerField('Geçerlilik Süresi (gün, 0=süresiz)', 
                                 validators=[Optional(), NumberRange(min=0, max=365)],
                                 default=30)
    submit = SubmitField('Kod Oluştur')

    def validate_code(self, code):
        existing = RegistrationCode.query.filter_by(code=code.data).first()
        if existing:
            raise ValidationError('Bu kod zaten mevcut.')


class StageChangeForm(FlaskForm):
    stage_id = SelectField('Yeni Etap', coerce=int, validators=[DataRequired()])
    start_day = IntegerField('Etabın Kaçıncı Günü', validators=[Optional()], default=1)
    notes = TextAreaField('Notlar', validators=[Optional(), Length(max=500)])
    submit = SubmitField('Etabı Değiştir')


class PatientProfileForm(FlaskForm):
    nickname = StringField('Ad / Rumuz', validators=[DataRequired(), Length(max=100)])
    phone = StringField('Telefon', validators=[Optional(), Length(max=20)])
    gender = SelectField('Cinsiyet', choices=[('', 'Belirtmek istemiyorum'),
                                               ('female', 'Kadın'), ('male', 'Erkek')],
                          validators=[Optional()])
    height_cm = FloatField('Boy (cm)', validators=[Optional(), NumberRange(min=50, max=250)])
    start_weight = FloatField('Başlangıç Kilosu (kg)', validators=[Optional(), NumberRange(min=20, max=500)])
    submit = SubmitField('Güncelle')
