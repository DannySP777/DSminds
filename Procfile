web: python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi:application
worker: python manage.py run_scheduler
