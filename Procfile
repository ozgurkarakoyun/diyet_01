web: flask db upgrade && python seed_stages.py && gunicorn "app:create_app()" --bind 0.0.0.0:$PORT --workers 2 --timeout 120
