# gensurv_project settings

`settings.py` is intentionally **not** committed (it's in `.gitignore`) - it
holds real production credentials (secret key, database password, email
password). To set up a deployment:

```
cp settings_template.py settings.py
```

Then fill in every `CHANGE-ME` placeholder in `settings.py`:

- `SECRET_KEY` - generate one with
  `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`
- `ALLOWED_HOSTS` / `CSRF_TRUSTED_ORIGINS` / `SITE_URL` / `CORS_ALLOWED_ORIGINS` -
  your real domain
- `DATABASES` - your Postgres name/user/password
- `MEDIA_ROOT` / `BACTOPIA_REPORT_PATH` / `DBBACKUP_STORAGE_OPTIONS` - real
  absolute paths on your server
- `EMAIL_HOST_USER` / `EMAIL_HOST_PASSWORD` / `DEFAULT_FROM_EMAIL` /
  `ADMIN_EMAIL` - your sending email account and app password

Setting up a local test copy instead? See
`docs/laptop_test_setup/TUTORIAL.md`, which uses its own sanitized
`settings_local_template.py` geared toward a laptop/no-real-data setup.
