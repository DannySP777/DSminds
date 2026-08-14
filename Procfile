web: gunicorn config.wsgi:application
worker: python manage.py run_scheduler
release: python manage.py migrate --noinput
