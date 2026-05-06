"""Production-safe stage seed script.
Creates only diet stages, not demo users/patients.
Usage: python seed_stages.py
"""
from app import create_app, db
from app.models import DietStage
from seed import STAGE1_DESC, STAGE2_DESC, STAGE3_DESC, STAGE4_DESC, FREE_DAY_DESC


def seed_stages():
    stages = [
        dict(stage_number=1, name='Saf Protein', duration_days=4,
             description=STAGE1_DESC, is_free_day=False, order=1),
        dict(stage_number=2, name='Protein + Çiğ Sebze', duration_days=5,
             description=STAGE2_DESC, is_free_day=False, order=2),
        dict(stage_number=3, name='Protein + Sebze + Pişmiş Sebze', duration_days=5,
             description=STAGE3_DESC, is_free_day=False, order=3),
        dict(stage_number=4, name='Çalma + Saf Protein', duration_days=7,
             description=STAGE4_DESC, is_free_day=False, order=4),
        dict(stage_number=0, name='Serbest Gün', duration_days=1,
             description=FREE_DAY_DESC, is_free_day=True, order=5),
    ]

    for data in stages:
        stage = DietStage.query.filter_by(stage_number=data['stage_number']).first()
        if stage:
            for key, value in data.items():
                setattr(stage, key, value)
        else:
            db.session.add(DietStage(**data))
    db.session.commit()


if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        seed_stages()
        print('Diet stages seeded/updated.')
