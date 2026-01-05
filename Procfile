web: gunicorn elibrary.wsgi --log-file -
release: python manage.py migrate
worker: celery -A elibrary worker -l info
beat: celery -A elibrary beat -l info
