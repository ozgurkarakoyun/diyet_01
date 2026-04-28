from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import current_user
from app import db

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_dietitian():
            return redirect(url_for('dietitian.dashboard'))
        elif current_user.is_patient():
            return redirect(url_for('patient.dashboard'))
    return redirect(url_for('auth.login'))


@main_bp.route('/run-migration-x7k2')
def run_migration():
    """One-time migration: personal_program sütunu ekle."""
    results = []
    try:
        with db.engine.connect() as conn:
            conn.execute(db.text(
                "ALTER TABLE patients ADD COLUMN IF NOT EXISTS personal_program TEXT"
            ))
            conn.commit()
        results.append('✅ personal_program sütunu eklendi (veya zaten vardı)')
    except Exception as e:
        results.append(f'❌ Hata: {str(e)}')
    return jsonify({'results': results})
