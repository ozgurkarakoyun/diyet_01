import os
import click
from app import create_app, db
from app.models import User, Dietitian

app = create_app()


@app.cli.command('seed')
def seed_command():
    """Veritabanina ornek veri yukle."""
    from seed import seed
    seed()


@app.cli.command('create-admin')
@click.argument('email')
@click.argument('name')
@click.argument('password')
def create_admin(email, name, password):
    """Yeni diyetisyen olustur. Kullanim: flask create-admin email Ad sifre"""
    existing = User.query.filter_by(email=email).first()
    if existing:
        click.echo(f'HATA: {email} zaten kayitli.')
        return
    user = User(email=email, role='dietitian')
    user.set_password(password)
    db.session.add(user)
    db.session.flush()
    dietitian = Dietitian(user_id=user.id, name=name)
    db.session.add(dietitian)
    db.session.commit()
    click.echo(f'Diyetisyen olusturuldu: {email}')


@app.context_processor
def inject_globals():
    from datetime import datetime
    return dict(now=datetime.utcnow)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV', 'development') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
