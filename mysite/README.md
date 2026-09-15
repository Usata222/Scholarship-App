# Scholarra

A scholarship discovery platform built with Django — where students find, filter, save, and apply to verified scholarships, and a single admin manages listings, reviews submissions, and sends newsletters through a custom-built dashboard.

---

## Demo / Screenshots

**Live demo:** _add your Render URL here once deployed_

<!-- Replace the lines below with your actual image paths or URLs -->

**Homepage**
![Homepage Screenshot](screenshots/homepage.png)

**Scholarship Detail Page**
![Detail Screenshot](screenshots/detail.png)

**Admin Dashboard**
![Dashboard Screenshot](screenshots/dashboard.png)

**Statistics Page**
![Statistics Screenshot](screenshots/statistics.png)

---

## Features

- **Scholarship Discovery** — Homepage with Hot Scholarships, Deadline Soon, and Latest Scholarships sections; filter by country, degree level, and funding type; pagination
- **Country Pages** — Browse all scholarships available in a specific country
- **Save/Bookmark** — Visitors can save scholarships without creating an account (session-based)
- **Click & View Tracking** — Every scholarship page view and "Apply Now" click is recorded for analytics
- **Share Button** — One-click WhatsApp sharing for social/TikTok traffic
- **Newsletter System** — Styled HTML emails, automatic notifications when a new scholarship is published (admin chooses via a "Save & Notify Subscribers" button), an admin composer for one-off broadcasts, and automated "closing soon" deadline reminders (triggered via a secret-protected URL for free external cron services)
- **Submit a Scholarship** — Public form for organizations to submit opportunities, with an admin review/approve/reject queue and email notifications
- **1-on-1 Coaching Requests** — Public contact form for application-support inquiries
- **Custom Admin Dashboard** (`/dashboard/`) — Session-based login (rate-limited against brute-force attempts), password reset, full CRUD for Scholarships and Countries, submission/coaching review queues, newsletter composer
- **Statistics / Analytics Page** — Date-range filtering, visitor trends (Chart.js), traffic sources, most-viewed/most-clicked scholarships with CTR, popular categories and destinations, search analytics including zero-result searches
- **SEO** — `robots.txt`, `sitemap.xml`, custom 404 page, canonical URLs, Open Graph tags, favicon
- **Privacy & Consent** — Privacy Policy and Terms of Use pages, consent checkboxes on public forms
- **Responsive Design** — Mobile-friendly UI with a hamburger navigation menu on small screens

---

## Technologies Used

| Layer | Technology |
|---|---|
| Backend | Python 3, Django (plain templates — no DRF/React) |
| Database | PostgreSQL (production) / SQLite (local & showcase deploys) |
| Email | Gmail SMTP, styled HTML emails via Django's `EmailMultiAlternatives` |
| Rate Limiting | `django-ratelimit` |
| Charts | Chart.js (via CDN) |
| Frontend | Django Templates, custom CSS design system, vanilla JS |
| Static Files | WhiteNoise |
| Deployment | Render (Gunicorn + WhiteNoise) |
| Auth | Django built-in authentication (single admin account) |

---

## Installation & Setup

### Prerequisites
- Python 3.10+
- pip
- Git

### Steps

**1. Clone the repository**
```bash
git clone https://github.com/your-username/scholarra.git
cd scholarra/mysite
```

**2. Create and activate a virtual environment**
```bash
python -m venv env

# On Mac/Linux
source env/bin/activate

# On Windows
env\Scripts\activate
```

**3. Install dependencies**
```bash
pip install -r requirements.txt
```

**4. Create your `.env` file**

Create a file called `.env` inside `mysite/` and fill in your values (see [Environment Variables](#environment-variables) below).

**5. Run database migrations**
```bash
python manage.py migrate
```

**6. Create a superuser (required for admin dashboard access)**
```bash
python manage.py createsuperuser
```

**7. (Optional) Seed demo scholarships**
```bash
python manage.py seed_demo_data
```

**8. Start the development server**
```bash
python manage.py runserver
```

Visit `http://127.0.0.1:8000` for the public site, `http://127.0.0.1:8000/dashboard/login/` for the admin.

---

## Environment Variables

This project uses a `.env` file for sensitive credentials. **Never commit this file to GitHub.**

Create a `.env` file with the following variables:

```env
# Django
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
SITE_URL=http://127.0.0.1:8000

# Database
DB_NAME=your_db_name
DB_USER=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=your_db_host
DB_PORT=5432

# Email
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_gmail_app_password
ADMIN_EMAIL=your_email@gmail.com

# Deadline reminder cron endpoint
DEADLINE_REMINDER_SECRET=a-long-random-string
```

### Where to get each value

| Variable | Where to get it |
|---|---|
| `SECRET_KEY` | Generate one at [djecrety.ir](https://djecrety.ir) or run `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"` |
| `DB_*` | Your local Postgres install, or your Render Postgres instance's connection details |
| `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` | A Gmail account with 2-Step Verification enabled, then an **App Password** generated at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords) — not your normal Gmail password |
| `ADMIN_EMAIL` | Where submission/coaching notifications go, and the public contact email shown site-wide |
| `DEADLINE_REMINDER_SECRET` | Any long random string — generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |

> ⚠️ For production (e.g. Render), set `DEBUG=False`, use your real domain for `ALLOWED_HOSTS` and `SITE_URL`, and add all of these same variables in your hosting platform's Environment tab.

---

## How to Use

### As a Visitor
1. **Browse** scholarships on the homepage, or filter by country, degree level, and funding type
2. **Save** a scholarship to revisit later (no account needed — saved via your browser session)
3. **Apply** — click "Apply Now" to go to the official application page
4. **Share** a scholarship via the WhatsApp button
5. **Subscribe** to the newsletter for alerts on new scholarships and closing-soon reminders
6. **Submit a Scholarship** if you represent an organization with an opportunity to list
7. **Request Coaching** for 1-on-1 application support

### As the Admin
1. Log in at `/dashboard/login/`
2. **Dashboard** — quick stats overview
3. **Scholarships** — add, edit, delete; "Save" just saves, "Save & Notify Subscribers" also emails your newsletter list
4. **Countries** — manage the list of study destinations
5. **Submissions** — review, approve, or reject organization-submitted scholarships
6. **Coaching Requests** — view incoming coaching inquiries
7. **Send Newsletter** — compose and broadcast a one-off email to all subscribers
8. **Statistics** — view visitor trends, traffic sources, top-performing scholarships, and search analytics with a date-range filter

---

## Deployment

This project is designed for **Render**. Key production setup:

- `DEBUG=False` in environment variables
- Gunicorn as the WSGI server (`gunicorn mysite.wsgi:application`)
- WhiteNoise for static file serving (`collectstatic` runs as part of the build command)
- `ALLOWED_HOSTS` and `SITE_URL` set to your real Render/custom domain
- Deadline reminder emails require a free external cron service (e.g. [cron-job.org](https://cron-job.org)) to ping `/cron/send-deadline-reminders/?key=...` once a day, since Render's free tier has no built-in scheduler
- All `.env` variables added manually in Render's Environment tab

---

## License

This project is open source and available under the [MIT License](LICENSE).
