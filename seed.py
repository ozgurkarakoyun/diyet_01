"""
Seed script – Veritabanına başlangıç verilerini yükler.
Kullanım:
    flask seed
    veya
    python seed.py
"""
from datetime import date, timedelta
from app import create_app, db
from app.models import (User, Dietitian, Patient, DietStage,
                        PatientStageHistory, RegistrationCode,
                        Measurement, Supplement, Message)

STAGE1_DESC = (
    "YENEBILECEKLER:\n"
    "Tavuk, tavuk ciğer, hindi eti, hindi boyun, hindi ciğer, hindi füme\n"
    "Taze balık, Dardanel ton balığı\n"
    "Kırmızı et, Adana döner (ekmeksiz), Köfte (ekmeksiz, unsuz)\n"
    "Pastırma, sucuk, kavurma\n"
    "Yumurta (her öğün – haşlanmış tercih edilir)\n"
    "Mantar\n\n"
    "Pişirme: Izgara tercih edilir. Az yağ ile tavada da yapılır.\n"
    "Sabah: Küçük kase yoğurt + 1 kaşık Vitalif yulaf ezmesi.\n"
    "Öğle & akşam: Küçük kase yoğurt ekleyin.\n"
    "Öğle & akşam: Bir kase mercimek veya sebze çorbası içebilirsiniz (unsuz, patates/havuç yasak)."
)

STAGE2_DESC = (
    "1. ETAPTAKI HER ŞEY GEÇERLİ + ÇİĞ SEBZELER EKLENİYOR:\n\n"
    "Roka, tere, nane, maydanoz, salatalık, turp, biber\n"
    "Semizotu, kereviz, yeşil soğan, kıvırcık, marul\n"
    "Az domates, avokado, mor ve beyaz lahana\n\n"
    "YASAK: Havuç, dereotu\n\n"
    "Öğle/akşam yoğurdu cacık yapılabilir.\n"
    "Salata: bol yeşillik, bol zeytinyağı, az domates."
)

STAGE3_DESC = (
    "1. VE 2. ETAP + EKLEMELER:\n\n"
    "Kahvaltıya: Peynir, zeytin (yeşil-siyah), 3 ceviz, 7 badem\n\n"
    "Öğle & akşama pişmiş sebze:\n"
    "Kabak, patlıcan, biber, yeşil fasulye, bamya, enginar\n\n"
    "YASAK: Patates, havuç, bezelye, kızartmanın her türü\n\n"
    "Buharda pişmiş tercih edilir.\n"
    "Öğün oranı: %40 et – %30 salata – %30 tencere yemeği"
)

STAGE4_DESC = (
    "4 ÇALMA GÜNÜ + 3 SAF PROTEİN GÜNÜ = 7 GÜN\n"
    "SIRA: Çalma → Saf Protein → Çalma → Saf Protein (birer gün arayla)\n\n"
    "ÇALMA KAHVALTI:\n"
    "3 kuru kayısı | Yulaf ezmeli yoğurt | Bir küçük meyve\n"
    "İnce bir dilim ekmek\n"
    "Yumurta, pastırma, sucuk, zeytin, peynir, yeşillikler\n\n"
    "ÇALMA ÖĞLE:\n"
    "3 kaşık bakliyat | 3 kaşık bulgur veya pirinç pilavı\n"
    "YA DA: küçük meyve / fındık lahmacun / küçük ekmek / 3 saçma / küçük dolma\n"
    "Küçük kase yoğurt | Bol yeşillikli zeytinyağlı salata\n\n"
    "ÇALMA AKŞAM:\n"
    "%40 protein | %30 salata | %30 yoğurt (cacık)\n\n"
    "SAF PROTEİN GÜNLERİ: 1. Etap menüsü uygulanır."
)

FREE_DAY_DESC = (
    "SERBEST GÜN!\n\n"
    "Bu gün istediğinizi yiyebilirsiniz.\n"
    "Yarın 1. Etap'tan tekrar başlıyorsunuz.\n\n"
    "Bir döngüyü daha tamamladınız. Başarılar!"
)


def seed():
    app = create_app()
    with app.app_context():
        print("Seed başlıyor...")

        # Diet Stages
        if DietStage.query.count() == 0:
            stages = [
                DietStage(stage_number=1, name='Saf Protein',
                          duration_days=4, description=STAGE1_DESC,
                          is_free_day=False, order=1),
                DietStage(stage_number=2, name='Protein + Çiğ Sebze',
                          duration_days=5, description=STAGE2_DESC,
                          is_free_day=False, order=2),
                DietStage(stage_number=3, name='Protein + Sebze + Pişmiş Sebze',
                          duration_days=5, description=STAGE3_DESC,
                          is_free_day=False, order=3),
                DietStage(stage_number=4, name='Çalma + Saf Protein',
                          duration_days=7, description=STAGE4_DESC,
                          is_free_day=False, order=4),
                DietStage(stage_number=0, name='Serbest Gün',
                          duration_days=1, description=FREE_DAY_DESC,
                          is_free_day=True, order=5),
            ]
            db.session.add_all(stages)
            db.session.commit()
            print("Etaplar olusturuldu.")
        else:
            print("Etaplar zaten var, atlaniyor.")

        # Demo Dietitian
        demo_d = User.query.filter_by(email='diyetisyen@demo.com').first()
        if not demo_d:
            d_user = User(email='diyetisyen@demo.com', role='dietitian')
            d_user.set_password('demo1234')
            db.session.add(d_user)
            db.session.flush()

            dietitian = Dietitian(
                user_id=d_user.id, name='Vedat Hoca',
                phone='555-000-0000', bio='Vedat Hoca diyetisyen hesabi'
            )
            db.session.add(dietitian)
            db.session.flush()

            for c in ['DEMO001', 'DEMO002', 'DEMO003', 'HASTA001', 'HASTA002']:
                db.session.add(RegistrationCode(code=c, dietitian_id=dietitian.id))
            db.session.commit()
            print("Vedat Hoca diyetisyen hesabi olusturuldu. (diyetisyen@demo.com / demo1234)")
        else:
            dietitian = demo_d.dietitian
            
            if dietitian and dietitian.name == 'Demo Diyetisyen':
                dietitian.name = 'Vedat Hoca'
                db.session.commit()
                print("Demo diyetisyen adi Vedat Hoca olarak guncellendi.")
            else:
                print("Vedat Hoca diyetisyen hesabi zaten var.")

        # Demo Patient
        demo_p = User.query.filter_by(email='hasta@demo.com').first()
        if not demo_p and dietitian:
            stage1 = DietStage.query.filter_by(stage_number=1).first()
            code_obj = RegistrationCode.query.filter_by(code='DEMO001', is_used=False).first()

            p_user = User(email='hasta@demo.com', role='patient')
            p_user.set_password('demo1234')
            db.session.add(p_user)
            db.session.flush()

            patient = Patient(
                user_id=p_user.id, dietitian_id=dietitian.id,
                nickname='Ayse H.', gender='female',
                height_cm=165, start_weight=78.5,
                current_stage_id=stage1.id if stage1 else None,
                stage_start_date=date.today() - timedelta(days=2),
                cycle_number=1
            )
            db.session.add(patient)
            db.session.flush()

            if code_obj:
                code_obj.is_used = True
                code_obj.used_by_patient_id = patient.id

            if stage1:
                db.session.add(PatientStageHistory(
                    patient_id=patient.id, stage_id=stage1.id,
                    start_date=date.today() - timedelta(days=2),
                    cycle_number=1, changed_by='auto'
                ))

            # Measurements
            for i in range(3):
                db.session.add(Measurement(
                    patient_id=patient.id,
                    date=date.today() - timedelta(days=10 - i * 5),
                    boyun=35.0 - i * 0.3, ust_gogus=92.0 - i * 0.5,
                    gogus=98.0 - i * 0.8, alt_gogus=89.0 - i * 0.6,
                    gobek=95.0 - i * 1.2, bel=82.0 - i * 1.0,
                    kalca=105.0 - i * 0.9, sag_kol=32.0 - i * 0.2,
                    sol_kol=31.5 - i * 0.2, sag_bacak=58.0 - i * 0.5,
                    sol_bacak=57.5 - i * 0.5, weight=78.5 - i * 1.2,
                    stage_id=stage1.id if stage1 else None
                ))

            # Supplement
            db.session.add(Supplement(
                patient_id=patient.id, dietitian_id=dietitian.id,
                product_name='Omega-3 Balik Yagi',
                description='Gunde 2 kapsul balik yagi',
                usage_instructions='Sabah ve aksam yemeklerinden sonra 1 kapsul',
                usage_time='Sabah & Aksam yemekten sonra',
                start_date=date.today(), is_active=True
            ))

            # Messages
            db.session.add(Message(
                content='Merhaba, programa hosgeldiniz! Sorulariniz icin mesaj atabilirsiniz.',
                sender_type='dietitian',
                sender_dietitian_id=dietitian.id,
                receiver_patient_id=patient.id
            ))
            db.session.add(Message(
                content='Tesekkurler hocam! 1. etap cok iyi gidiyor.',
                sender_type='patient',
                sender_patient_id=patient.id,
                receiver_dietitian_id=dietitian.id
            ))
            db.session.commit()
            print("Demo hasta olusturuldu. (hasta@demo.com / demo1234)")
        else:
            print("Demo hasta zaten var.")

        print("\nSeed tamamlandi!")
        print("-" * 40)
        print("Vedat Hoca : diyetisyen@demo.com / demo1234")
        print("Hasta      : hasta@demo.com / demo1234")
        print("Kayit kodlari: DEMO001-003, HASTA001-002")


if __name__ == '__main__':
    seed()
