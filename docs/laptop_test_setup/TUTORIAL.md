# Setting up Gensurv on your laptop for testing

This gets you a fully working local copy of the site — separate from
production, with its own local database and no real data. Nothing here can
affect the live site.

You'll need: **git**, **Node.js** (v18+), and either **miniforge/mamba**
(recommended - handles Python + Postgres for you) or your own Python 3.12 +
PostgreSQL install.

## 1. Clone the repo

```
git clone <the GitHub repo URL> Gensurv
cd Gensurv
```

## 2. Backend: Python environment

```
cd backend
mamba env create -f ../environment.yml
mamba activate gensurv
```

(If you don't use conda/mamba: create a Python 3.12 venv and
`pip install -r ../requirements.pip.txt` instead - you'll also need
PostgreSQL installed separately in that case.)

## 3. Local database (no production credentials involved)

The `environment.yml` you just installed includes PostgreSQL itself, so you
don't need a system-wide install. Initialize a small local instance that
lives entirely inside your project folder:

```
# from the backend/ folder, with the gensurv env active
initdb -D ./pgdata
pg_ctl -D ./pgdata -l ./pgdata/log.txt start

createuser -s gensurv_user_local
createdb -O gensurv_user_local gensurv_db_local
psql -d gensurv_db_local -c "ALTER USER gensurv_user_local WITH PASSWORD 'choose-your-own-local-password';"
```

(Already have Postgres installed system-wide instead? Just run the last
three commands against your existing server - skip `initdb`/`pg_ctl`.)

To stop the local database later: `pg_ctl -D ./pgdata stop`

## 4. Settings file

The real `settings.py` is intentionally not in GitHub (`.gitignore`) since
it has production secrets. Use the sanitized local version instead:

```
cp /path/to/settings_local_template.py gensurv_project/settings.py
```

Then edit two things in the new `settings.py`:
- `PASSWORD` in the `DATABASES` block - match whatever you set in step 3.
- `SECRET_KEY` - generate your own, don't use the placeholder:
  ```
  python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
  ```
  Paste the output in as `SECRET_KEY`.

## 5. Run migrations and create your own admin user

```
python manage.py migrate
python manage.py createsuperuser
```

## 6. Start the backend

```
python manage.py runserver
```

Leave this running - it serves the API on `http://127.0.0.1:8000`.

## 7. Frontend

In a **new terminal**:

```
cd Gensurv/frontend
npm install
npm run dev
```

This starts the Vite dev server (usually `http://localhost:5173`) and
automatically proxies `/api/...` requests to the Django server from step 6
(see `vite.config.js`) - no CORS setup needed.

## 8. Open it

Go to `http://localhost:5173` in a browser, log in with the superuser you
created in step 5.

## What won't work locally (and that's expected)

- **No real submission data, no Bactopia results.** The Dashboard/Results
  pages will just be empty until you upload something yourself through the
  UI. The Results Dashboard's QC pass/fail info depends on a
  `bactopia-report.tsv` file that doesn't exist locally - it degrades
  gracefully (everything just shows "pending"), it won't error.
- **Password reset emails print to your terminal** instead of actually
  sending (see the `runserver` console output) - `EMAIL_BACKEND` is set to
  the console backend on purpose, so no real email credentials are needed.
- **No nginx/gunicorn** - `manage.py runserver` + Vite's dev server are
  fine for testing the app itself. You only need those for a
  production-style deployment, which this tutorial deliberately skips.
