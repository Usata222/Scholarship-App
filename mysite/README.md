# Scholarra

A scholarship discovery site built with Django (plain templates, no DRF/React). Students browse, filter, save, and apply to scholarships. A single admin manages content through a custom dashboard at `/dashboard/`.

## Features

- Public site: homepage with Hot/Deadline Soon sections, filters (country, degree level, funding type), pagination, country pages, scholarship detail pages
- Session-based save/bookmark (no account required)
- Click tracking on "Apply Now" and view counts per scholarship
- WhatsApp share button
- Newsletter signup with **styled HTML emails** (not plain text) — automatically sent to subscribers when a scholarship is published, plus a **"Send Newsletter" composer in the admin dashboard** for one-off broadcast emails, with unsubscribe links in every email
- Public "Submit a Scholarship" form with admin review/approve/reject + email notifications
- Public "Request Coaching" contact form
- Custom admin dashboard (`/dashboard/`) — session-based login, rate-limited (5 attempts/min), password reset, full CRUD for Scholarships and Countries, submission/coaching review queues, newsletter composer
- Consistent design system (`myapp/static/myapp/style.css`), responsive layout, shared public/dashboard base templates
- Privacy Policy and Terms of Use pages, consent checkboxes on public forms
- SEO basics: `robots.txt`, `sitemap.xml`, custom 404 page, favicon, canonical URLs, Open Graph tags on scholarship pages
- **Admin Statistics page** (`/dashboard/statistics/`) — date-range filter (today/7/30/90 days), overview cards with period-over-period comparison, a visitor trend chart (Chart.js via CDN, no extra frontend framework), traffic sources, most-viewed and most-clicked scholarships with CTR, popular categories and study destinations, and search/filter analytics including zero-result searches (a direct signal for content gaps). Built on one new model, `AnalyticsEvent`, that logs page views, scholarship views, application clicks, searches, and saves as they happen.
- Contact email everywhere on the site (footer, privacy policy, terms) is pulled automatically from `ADMIN_EMAIL` in `.env` via a context processor — change it in one place, it updates everywhere

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

### Seeding demo data

To quickly populate the homepage with realistic sample scholarships (useful for demos/testing):

```bash
python manage.py seed_demo_data
```

This creates 7 real-world-style scholarships (DAAD, Chevening, Vanier, Holland Scholarship, Fulbright, Australia Awards, MEXT) across 7 countries, all published. It's safe to run more than once — it skips anything that already exists rather than duplicating it. Note: seeded scholarships have no image attached; add one manually per scholarship in the admin if you want the card images to show.

## Environment Variables (`mysite/.env`)

| Variable | Purpose |
|---|---|
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Postgres connection |
| `SECRET_KEY` | Django's cryptographic signing key — keep this secret, never commit it |
| `DEBUG` | `True` locally, **must be `False` in production** |
| `ALLOWED_HOSTS` | Comma-separated list, e.g. `scholarra.com,www.scholarra.com` |
| `SITE_URL` | Base URL used to build links inside emails (unsubscribe, "view scholarship"). Set to your real domain in production. |
| `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD` | Gmail SMTP credentials (use an App Password, not your real password) |
| `ADMIN_EMAIL` | Where submission/coaching notifications are sent, and what shows as the site's public contact email |

`.env` is git-ignored — never commit it. (It is intentionally **not** included in project handoffs/zips — recreate it locally using the table above.)

## Known Gaps / Not Yet Built

Deliberately deferred, not forgotten:

- **Rate limiting** is applied to admin login only (5 attempts/min, `django-ratelimit` with `LocMemCache`). Submission form and click-tracking redirect are intentionally *not* rate-limited — a deliberate decision after weighing the actual risk (submissions require admin approval before going live; clicks only affect an internal analytics number).
- **Visitor country / IP geolocation** — the Statistics page tracks visitor counts, page views, traffic sources, and scholarship performance, but does NOT show visitor countries. Adding that needs an external geolocation service or database, deliberately left out of the first version to avoid unneeded infrastructure. Add it later if it becomes genuinely useful.
- **UTM campaign tracking works, but only for links you tag.** TikTok/Instagram's in-app browsers often strip the referrer header, so untagged social links usually show as "Direct/Unknown" in Traffic Sources. Get in the habit of adding `?utm_source=tiktok&utm_campaign=...` to any link you post, or that traffic won't be attributable.
- **2FA on the admin account** — deliberately not built; a single strong, non-reused password is the current line of defense.
- **Slug collisions on auto-approved submissions** — if an approved submission's auto-generated slug collides with an existing one, saving will fail. Low risk at low volume; needs a real fix (auto-suffixing) before high submission volume.
- **Newsletter sending is synchronous** — fine at current subscriber counts; would need a background task queue (e.g. Celery) if the list grows into the hundreds/thousands. This applies to both the automatic new-scholarship email and the manual newsletter composer.
- **Consent checkboxes are client-side only** (`required` attribute) — not enforced server-side. Acceptable for MVP; a determined bad actor could bypass via a raw POST request.
- **`LocMemCache` (used for rate limiting) is per-process** — fine for local dev / a single production worker process; if you deploy with multiple gunicorn workers, each worker counts attempts separately, weakening the limit. Upgrade to Redis if that becomes a real deployment shape.

## Deploying (e.g. to Render)

1. Set all environment variables above in your host's dashboard — especially `DEBUG=False`, real `ALLOWED_HOSTS`, and `SITE_URL` set to your actual domain.
2. Run `python manage.py collectstatic --noinput` as part of your build step (static files are served via WhiteNoise, already configured in `settings.py`).
3. Run `python manage.py migrate` on deploy.
4. Use `gunicorn mysite.wsgi:application` as your start command (already in `requirements.txt`).
5. Double-check the email backend works from your production environment — some hosts block outbound SMTP on certain ports.
6. If you want demo content on the live site immediately, run `python manage.py seed_demo_data` once after migrating.
