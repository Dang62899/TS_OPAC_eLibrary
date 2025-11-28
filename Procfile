web: gunicorn elibrary.wsgi:application --log-file -
worker: celery -A elibrary worker -l info
beat: celery -A elibrary beat -l info
