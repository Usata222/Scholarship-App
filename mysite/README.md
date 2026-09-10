# ScholarHub

A scholarship discovery site built with Django (plain templates, no DRF/React). Students browse, filter, save, and apply to scholarships. A single admin manages content through a custom dashboard at `/dashboard/`.

## Features

- Public site: homepage with Hot/Deadline Soon sections, filters (country, degree level, funding type), pagination, country pages, scholarship detail pages
- Session-based save/bookmark (no account required)
- Click tracking on "Apply Now" and view counts per scholarship
- WhatsApp share button, newsletter signup with email alerts on new publications + unsubscribe
- Public "Submit a Scholarship" form with admin review/approve/reject + email notifications
- Public "Request Coaching" contact form
- Custom admin dashboard (`/dashboard/`) — session-based login, password reset, full CRUD for Scholarships and Countries, submission/coaching review queues
- Consistent design system (`myapp/static/myapp/style.css`), responsive layout, shared public/dashboard base templates
- Privacy Policy and Terms of Use pages, consent checkboxes on public forms

## Local Setup

```bash
cd mysite
python -m venv env
env\Scripts\activate        # Windows
pip install -r requirements.txt
```

Create/edit `mysite/.env` (see **Environment Variables** below), then:

```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the public site, `http://127.0.0.1:8000/dashboard/login/` for the admin.

## Environment Variables (`mysite/.env`)

| Variable | Purpose |
|---|---|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Postgres connection |
| `SECRET_KEY` | Django's cryptographic signing key — keep this secret, never commit it |
| `DEBUG` | `True` locally, **must be `False` in production** |
| `ALLOWED_HOSTS` | Comma-separated list, e.g. `scholarhub.com,www.scholarhub.com` |
| `SITE_URL` | Base URL used to build links inside emails (unsubscribe, "view scholarship"). Set to your real domain in production. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail SMTP credentials (use an App Password, not your real password) |
| `ADMIN_EMAIL` | Where submission/coaching notifications are sent |

`.env` is git-ignored — never commit it.

## Known Gaps / Not Yet Built

These were deliberately deferred, not forgotten:

- **Rate limiting** — the login page, submission form, and click-tracking redirect currently have no protection against abuse. This is the single most important thing to add before real public traffic.
- **SEO basics** — `robots.txt`, `sitemap.xml`, custom 404 page, canonical URLs are not yet built (basic meta descriptions and Open Graph tags on the scholarship detail page are in place).
- **2FA on the admin account** — deliberately not built; a single strong, non-reused password is the current line of defense. Revisit if this becomes a multi-admin system.
- **Slug collisions on auto-approved submissions** — if an approved submission's auto-generated slug collides with an existing one, saving will fail. Low risk at low volume; needs a real fix (auto-suffixing) before high submission volume.
- **Newsletter sending is synchronous** — fine at current subscriber counts; would need a background task queue (e.g. Celery) if the list grows into the hundreds/thousands.
- **Consent checkboxes are client-side only** (`required` attribute) — not enforced server-side. Acceptable for MVP; a determined bad actor could bypass via a raw POST request.

## Deploying (e.g. to Render)

1. Set all environment variables above in your host's dashboard — especially `DEBUG=False`, real `ALLOWED_HOSTS`, and `SITE_URL` set to your actual domain.
2. Run `python manage.py collectstatic --noinput` as part of your build step (static files are served via WhiteNoise, already configured in `settings.py`).
3. Run `python manage.py migrate` on deploy.
4. Use `gunicorn mysite.wsgi:application` as your start command (already in `requirements.txt`).
5. Double-check the email backend works from your production environment — some hosts block outbound SMTP on certain ports.
