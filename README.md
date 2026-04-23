# 🥗 DiyetTakip – Diyetisyen-Hasta Takip Sistemi

Flask tabanlı, PostgreSQL destekli, Railway'e deploy edilebilir diyetisyen-hasta takip uygulaması.

## 📋 Özellikler

- **Diyetisyen Paneli**: Tüm hastaları yönet, etap değiştir, mesajlaş, takviye gönder
- **Hasta Paneli**: Etap takibi, ölçüm girişi, mesajlaşma, takviye görüntüleme
- **4 Etaplı Diyet Sistemi**: Otomatik etap geçişi + serbest gün döngüsü
- **Ölçüm Takibi**: 11 bölge ölçümü + grafiksel gösterim
- **Mesajlaşma**: Okundu/okunmadı sistemi ile anlık mesajlaşma
- **Kayıt Kodu Sistemi**: Diyetisyen onaylı hasta kaydı
- **Railway Deploy Hazır**: PostgreSQL + Gunicorn

---

## 🚀 Yerel Kurulum

### 1. Repoyu klonla

```bash
git clone https://github.com/kullaniciadi/dietapp.git
cd dietapp
```

### 2. Sanal ortam oluştur ve aktifleştir

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Bağımlılıkları yükle

```bash
pip install -r requirements.txt
```

### 4. Ortam değişkenlerini ayarla

```bash
cp .env.example .env
# .env dosyasını düzenle:
# SECRET_KEY → güçlü bir anahtar gir
# DIETITIAN_ADMIN_KEY → diyetisyen kaydı için şifre
```

### 5. Veritabanı migration

```bash
flask db init      # İlk kez
flask db migrate -m "initial"
flask db upgrade
```

### 6. Seed data yükle (demo veriler)

```bash
python seed.py
```

Seed sonrası oluşan demo hesaplar:

| Rol | E-posta | Şifre |
|-----|---------|-------|
| Diyetisyen | diyetisyen@example.com | Admin1234! |
| Hasta | hasta@example.com | Hasta1234! |

Demo kayıt kodları: `DEMO001`, `HASTA01`, `HASTA02`, `HASTA03`

### 7. Uygulamayı başlat

```bash
python run.py
```

Tarayıcıda aç: [http://localhost:5000](http://localhost:5000)

---

## 🩺 Diyetisyen Hesabı Oluşturma

Yeni diyetisyen hesabı için `/auth/register/dietitian` sayfasına git.  
`DIETITIAN_ADMIN_KEY` değeri ile kayıt olunur (varsayılan: `admin123`).

> ⚠️ Production'da `DIETITIAN_ADMIN_KEY` mutlaka değiştirilmeli!

---

## 🚂 Railway Deployment

### 1. Railway Hesabı ve Proje

1. [railway.app](https://railway.app) üzerinde hesap oluştur
2. **New Project → Deploy from GitHub repo** seç
3. Bu repoyu bağla

### 2. PostgreSQL Ekle

1. Railway projesinde **+ New → Database → PostgreSQL** ekle
2. Railway, `DATABASE_URL` ortam değişkenini otomatik sağlar

### 3. Ortam Değişkenlerini Ayarla

Railway dashboard → Variables sekmesine gir:

```
SECRET_KEY          = uzun-ve-rastgele-bir-deger-girin
DIETITIAN_ADMIN_KEY = gizli-admin-anahtari
FLASK_ENV           = production
```

> `DATABASE_URL` Railway tarafından otomatik eklenir, elle girme.

### 4. Deploy

Railway repoyu her `git push` sonrası otomatik deploy eder.  
`Procfile` içindeki komut otomatik çalışır:

```
web: gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120
```

### 5. Migration ve Seed (Railway üzerinde)

Railway dashboard → proje → **Settings → Deploy** bölümünden veya Railway CLI ile:

```bash
# Railway CLI kur
npm install -g @railway/cli
railway login
railway run flask db upgrade
railway run python seed.py
```

---

## 📁 Proje Yapısı

```
dietapp/
├── app/
│   ├── __init__.py          # Uygulama fabrikası
│   ├── models.py            # Veritabanı modelleri
│   ├── forms.py             # WTForms formları
│   ├── routes/
│   │   ├── auth.py          # Giriş/kayıt
│   │   ├── dietitian.py     # Diyetisyen route'ları
│   │   ├── patient.py       # Hasta route'ları
│   │   ├── main.py          # Ana yönlendirme
│   │   └── errors.py        # Hata sayfaları
│   ├── templates/
│   │   ├── base.html        # Ana şablon (sidebar, topbar)
│   │   ├── auth/            # Giriş/kayıt sayfaları
│   │   ├── dietitian/       # Diyetisyen şablonları
│   │   ├── patient/         # Hasta şablonları
│   │   └── errors/          # 403, 404, 500
│   └── static/              # CSS, JS, görseller
├── migrations/              # Flask-Migrate migration dosyaları
├── config.py                # Konfigürasyon sınıfları
├── run.py                   # Geliştirme sunucusu
├── seed.py                  # Demo veri scripti
├── requirements.txt
├── Procfile                 # Railway/Gunicorn
├── .env.example
├── .gitignore
└── README.md
```

---

## 🗄️ Veritabanı Modelleri

| Tablo | Açıklama |
|-------|----------|
| `users` | Tüm kullanıcılar (rol: dietitian/patient) |
| `dietitians` | Diyetisyen profilleri |
| `patients` | Hasta profilleri + aktif etap bilgisi |
| `diet_stages` | Etap tanımları (4 etap + serbest gün) |
| `patient_stage_history` | Etap geçiş geçmişi |
| `measurements` | 11 bölge vücut ölçümleri |
| `supplements` | Takviye / ek gıda kayıtları |
| `messages` | Diyetisyen-hasta mesajlaşma |
| `registration_codes` | Hasta kayıt kodları |

---

## 🔄 Diyet Döngüsü

```
1. Etap (4 gün) → 2. Etap (5 gün) → 3. Etap (5 gün) → 4. Etap (7 gün) → Serbest Gün → 1. Etap ...
```

- Etap geçişleri otomatiktir (her dashboard yüklenişinde kontrol edilir)
- Diyetisyen etabı istediği zaman manuel değiştirebilir
- Tüm değişiklikler `patient_stage_history` tablosuna kaydedilir

---

## 🔐 Güvenlik

- Şifreler `werkzeug.security` ile hash'lenir (PBKDF2-SHA256)
- CSRF koruması (Flask-WTF) tüm formlarda aktif
- Her hasta yalnızca kendi verisine erişebilir
- Diyetisyen yalnızca kendi hastalarını görebilir
- Rol bazlı yetkilendirme (dietitian / patient)
- Session cookie güvenliği production'da aktif

---

## 📊 Ölçüm Bölgeleri

Boyun · Üst Göğüs · Göğüs · Alt Göğüs · Göbek · Bel · Kalça · Sağ Kol · Sol Kol · Sağ Bacak · Sol Bacak

---

## 🛠️ Geliştirme

```bash
# Test çalıştır
python -m pytest tests/

# Migration oluştur
flask db migrate -m "açıklama"
flask db upgrade

# Shell
flask shell
```

---

## 📄 Lisans

MIT License
