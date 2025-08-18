# Gensurv
- End-to-end way to move Django + Gunicorn + Nginx + Postgres stack to a new server using your GitHub repo and a DB dump.

## 1) Prep the new server
### system deps (Ubuntu/Debian example)
```bash sudo apt update
sudo apt install -y python3 python3-venv python3-pip build-essential \
  libpq-dev nginx postgresql postgresql-contrib
```
### (optional) firewall
```bash sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

### 2) Create a project user & folder
```bash sudo adduser --system --group --home /srv/myproject myproject
sudo mkdir -p /srv/myproject/{app,venv,run,static,media}
sudo chown -R myproject:myproject /srv/myproject
```

### 3) Pull your code & set up Python env
```bash sudo -u myproject bash -lc '
cd /srv/myproject/app
git clone https://github.com/<you>/<repo>.git .
python3 -m venv /srv/myproject/venv
source /srv/myproject/venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
'
```

### 4) Configure secrets & settings
Create an environment file that Gunicorn will load:
```bash sudo -u myproject tee /srv/myproject/app/.env >/dev/null <<'EOF'
DJANGO_SETTINGS_MODULE=myproject.settings
SECRET_KEY=change-me
DEBUG=False
ALLOWED_HOSTS=my.domain.com,another.host
DATABASE_URL=postgres://myproject:supersecret@127.0.0.1:5432/myproject
# Any other envs your settings read (EMAIL_*, REDIS_URL, etc.)
EOF
```
Make sure your Django settings read from environment (e.g., via os.environ or django-environ).

### 5) Create Postgres DB & restore your dump
```sql sudo -u postgres psql <<'SQL'
CREATE USER myproject WITH PASSWORD 'supersecret';
CREATE DATABASE myproject OWNER myproject;
\q
SQL
```

#### Restore (pick the right command based on dump type):
- Plain SQL (file looks like readable SQL):
```bash psql -U myproject -h 127.0.0.1 -d myproject -f /path/to/dump.sql
```
- Custom/Directory format (.dump/.custom from pg_dump -Fc):
```bash pg_restore -U myproject -h 127.0.0.1 -d myproject -c /path/to/dump.custom
```
If you have uploaded media files, copy them into:
/srv/myproject/media/

### 6) Run Django admin tasks
```bash sudo -u myproject bash -lc '
source /srv/myproject/venv/bin/activate
cd /srv/myproject/app
python manage.py collectstatic --noinput
```
# If restoring a full DB snapshot that already has a schema, you usually skip migrations.
# Otherwise, run:
```bash python manage.py migrate
python manage.py check --deploy
'
```

### 7) Gunicorn systemd unit
Socket-based (recommended):
```vim
/etc/systemd/system/gunicorn-myproject.socket
[Unit]
Description=gunicorn socket for myproject

[Socket]
ListenStream=/srv/myproject/run/gunicorn.sock

[Install]
WantedBy=sockets.target
/etc/systemd/system/gunicorn-myproject.service
[Unit]
Description=gunicorn daemon for myproject
Requires=gunicorn-myproject.socket
After=network.target

[Service]
User=myproject
Group=myproject
WorkingDirectory=/srv/myproject/app
EnvironmentFile=/srv/myproject/app/.env
ExecStart=/srv/myproject/venv/bin/gunicorn myproject.wsgi:application \
  --workers 3 --bind unix:/srv/myproject/run/gunicorn.sock
Restart=always

[Install]
WantedBy=multi-user.target
Enable & start:
sudo systemctl daemon-reload
sudo systemctl enable --now gunicorn-myproject.socket
sudo systemctl start gunicorn-myproject.service
sudo systemctl status gunicorn-myproject.service
```

### 8) Nginx site config
/etc/nginx/sites-available/myproject
```bash 
server {
    server_name my.domain.com;

    # Max upload size if you accept uploads
    client_max_body_size 50M;

    location = /favicon.ico { access_log off; log_not_found off; }

    # Static & media
    location /static/ { alias /srv/myproject/static/; }
    location /media/  { alias /srv/myproject/media/;  }

    # Proxy to gunicorn (unix socket)
    location / {
        include proxy_params;
        proxy_pass http://unix:/srv/myproject/run/gunicorn.sock;
    }

    # Optional: security headers (tune as needed)
    add_header X-Content-Type-Options nosniff;
    add_header X-Frame-Options DENY;
    add_header Referrer-Policy strict-origin-when-cross-origin;
}
```
Enable & test:
```bash sudo ln -s /etc/nginx/sites-available/myproject /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 9) (Optional) HTTPS with Let’s Encrypt
If you have a domain pointing to the server:
```bash sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d my.domain.com
```

### 10) Verify & harden
App health:
```bash curl -I http://127.0.0.1/        # from server (should be 200 or 301/302)
sudo journalctl -u gunicorn-myproject.service -n 100 --no-pager
sudo tail -f /var/log/nginx/access.log /var/log/nginx/error.log
```
- Ensure DEBUG=False, correct ALLOWED_HOSTS, and a strong SECRET_KEY.
- If you used DATABASE_URL, confirm your settings parse it.
- If you use Celery/Redis/cron, migrate those services too (systemd units, env files).
- Set correct ownership: sudo chown -R myproject:myproject /srv/myproject.
- Quick “everything in one go” checklist
- Install OS deps (Python, libpq-dev, nginx, postgres).
- Create user and folders under /srv/myproject.
- Clone GitHub repo; create venv; pip install -r requirements.txt.
- Create .env with secrets and DB URL.
- Create Postgres user+db; restore dump.
- collectstatic, maybe migrate.
- Install Gunicorn systemd unit + socket.
- Configure Nginx (static/media + proxy to socket).
- Optional) TLS via certbot.
- Test, check logs, and tighten perms.
- Using repo layout (project name, settings.py path, static/media paths), tailor the unit and Nginx files exactly to the structure.
