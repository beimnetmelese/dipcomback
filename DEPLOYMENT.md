# Django Backend Deployment Guide

This backend is configured for production deployment with:

- Environment-driven settings
- MySQL database support
- WhiteNoise static file serving
- Gunicorn WSGI server
- Production security defaults

## 1. Install dependencies

```bash
pip install -r requirements.txt
```

## 2. Configure environment

Create `.env` in the backend root (same folder as `manage.py`) from `.env.example` and set real values.

Required minimum values:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=False`
- `DJANGO_ALLOWED_HOSTS`
- `MYSQL_DATABASE`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_HOST`
- `MYSQL_PORT`

## 3. Run migrations and collect static files

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

## 4. Validate deployment settings

```bash
python manage.py check --deploy
```

## 5. Run in production

```bash
gunicorn dipcom.wsgi:application --bind 0.0.0.0:8000
```

If your platform uses `Procfile`, it is already included.

## Notes

- `DB_ENGINE=mysql` is the default. Set `DB_ENGINE=sqlite` only for local quick testing.
- Static files are served from `STATIC_ROOT` (`staticfiles/`) with WhiteNoise.
- Media uploads are stored under `media/`.
- Ensure your reverse proxy forwards `X-Forwarded-Proto` so HTTPS redirects work correctly.
