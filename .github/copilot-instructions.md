## Quick orientation for AI coding agents

This repository is a small Django project (Django 5.2) named `institute_time`. It's an LMS-style app with one main app `accounts` and project configuration under the `core` package. The goal of this file is to help an AI agent be immediately productive when making changes.

- Project root files: `manage.py`, `requirements.txt`, `README.md`.
- Django settings: `core/settings.py` (uses environment variables via `core/envs/config.py`).
- Single app: `accounts/` (models, views, templates, urls live here).
- Templates: shared under `templates/` (e.g. `templates/base.html`, `templates/accounts/login.html`, `templates/dashboard/index.html`).
- Static and media: static files under `static/`, media uploads under `media/` (`MEDIA_ROOT` configured in `core/settings.py`).

Key contracts and runtime expectations
- The app requires a `.env` file at `core/envs/.env`. `core/envs/config.py` will exit the process if `.env` is missing — create it from `core/envs/.env.example` before running.
- Database: PostgreSQL. See `requirements.txt` (`psycopg2-binary`) and `core/settings.py` which reads DB config from the env vars `DATABASE_NAME`, `DATABASE_USERNAME`, `DATABASE_PASSWORD`, `DATABASE_HOST`, `DATABASE_PORT`.
- Custom user model: `accounts.models.CustomUser` is used via `AUTH_USER_MODEL`. Roles are stored in a JSONField `roles` and there is an `active_role` string.

Developer workflows (concrete commands)
- Create environment and install deps:
  - python -m venv .venv && source .venv/bin/activate
  - pip install -r requirements.txt
- Database setup (example): create a PostgreSQL DB and user as shown in `README.md`.
- Copy env example and fill credentials:
  - cp core/envs/.env.example core/envs/.env
  - edit `core/envs/.env` and set `SECRET_KEY`, `DEBUG`, DB vars, and `HEMIS` API vars.
- Run migrations and start dev server:
  - python manage.py migrate
  - python manage.py createsuperuser
  - python manage.py runserver

Important code patterns and conventions (do not change lightly)
- Role management: prefer using provided helper methods on `CustomUser`:
  - `user.has_role(role)`, `user.add_role(role)`, `user.remove_role(role)`, `user.set_active_role(role)`.
  - `create_superuser` bootstraps `roles` to `['admin','teacher','student']`.
- Views use Django's decorators: `@login_required` used in `core/urls.py` for the dashboard view and in `accounts.views` for logout/switch_role.
- Templates load static files via `{% load static %}` and expect the static folder layout shown in `static/` (css, js, favicon, images).

Integration points and external dependencies
- HEMIS API: configured via `HEMIS_API_TOKEN` and `HEMIS_UNIVERSITY_API_BASE_URL` in `core/envs/.env`. Code expects these env vars to exist.
- Admin: `admin.site` is customized in `core/urls.py` headers/titles.

When changing or adding behavior, inspect these files first
- `core/settings.py` — environment-driven config and static/media settings.
- `core/envs/config.py` — enforces `.env` presence and exposes runtime variables.
- `accounts/models.py` — CustomUser and role logic (authoritative source for user fields).
- `accounts/views.py` — login, logout and `switch_role` implementations (how roles are applied at runtime).
- Templates under `templates/` — UI expectations for login/dashboard/layout.

Edge cases & gotchas
- Missing `.env` will exit early (see `core/envs/config.py`), so tests/run steps will fail until `.env` is present.
- Static files are only served via `django.conf.urls.static` when `DEBUG=True`. For production, run `collectstatic` and configure a static file server.
- Timezone set to `Asia/Tashkent` in `core/settings.py`; keep awareness when adding time-aware logic.

Suggested minimal PR checklist for AI changes
1. If you modify settings/env usage, update `core/envs/.env.example` accordingly.
2. If you add DB fields, create and run migrations (`python manage.py makemigrations` + `migrate`).
3. Run the dev server and verify the login flow and dashboard render (create a superuser if needed).
4. When touching user/role logic, prefer existing `CustomUser` helpers to manipulate `roles` and `active_role`.

If anything above is unclear or you want more examples (e.g., navbar templates or role-switch UI), tell me which area to expand and I will update this file.
