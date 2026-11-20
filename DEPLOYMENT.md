# BYB V1 deployment

## Existing architecture

- `frontend/` is a Vite React/TypeScript application served as static assets.
- `backend/` is a Django REST API served by Gunicorn.
- PostgreSQL is hosted on Neon; user-uploaded images are stored in Cloudinary.
- Configure an SMTP provider for account verification and password reset email.

## Backend environment

Configure the variables in `backend/.env.example` in the deployment platform. Keep
`DJANGO_DEBUG=False`, use a unique random `DJANGO_SECRET_KEY`, set exact API
hostnames in `DJANGO_ALLOWED_HOSTS`, and set `DATABASE_URL` to the Neon
PostgreSQL connection string with TLS enabled. Supply Cloudinary credentials and
SMTP settings as secret environment variables. Set `CORS_ALLOWED_ORIGINS` and
`CSRF_TRUSTED_ORIGINS` to the exact deployed frontend origin(s). Do not commit
real environment files or credentials.

Run `python manage.py check --deploy` with the production environment before
launch. The API host must terminate HTTPS and forward `X-Forwarded-Proto: https`
for Django's proxy-aware secure settings. Configure body-size limits at the
reverse proxy to at least 12 MB to permit supported multipart image uploads.

## Build and release

From `backend/`, install `requirements.txt`, then run `python manage.py check`,
`python manage.py migrate --check`, and `python manage.py migrate --noinput`.
Apply migrations to a staging Neon branch and verify the application before
running them against production. Back up the production database first. Do not
run destructive schema operations as part of an automatic deploy.

Start the API with:

```sh
gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3 --timeout 60
```

Django static files use WhiteNoise. Run `python manage.py collectstatic --noinput`
as part of the backend release.

From `frontend/`, set `VITE_API_BASE_URL` to the API origin plus `/api` when the
API is cross-origin, then run `npm ci && npm run build` and publish `dist/` on
the existing static hosting platform. If frontend and backend share an origin,
the production default is `/api`.

## Manual launch checks

- Confirm the Neon production URL, backup/restore plan, and migration rehearsal.
- Confirm Cloudinary upload credentials, allowed formats and transformations.
- Verify SMTP delivery and domain authentication (SPF/DKIM/DMARC) end-to-end.
- Verify TLS, frontend/API origins, DNS, and proxy upload-size/time-out settings.
- Create and verify a BYB staff account; test event and Hub moderation in staging.
