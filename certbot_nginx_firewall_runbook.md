# Ops runbook: Certbot, Nginx & firewall sanity-checks (safe for multi-site servers)

Use this when you’re adding a new Django site on a box that already serves other sites. Everything below is non-disruptive.

---

## 1) Verify Certbot is installed and the Nginx plugin is available

```bash
which certbot
certbot --version
certbot plugins
```

**Healthy example (What I saw on the server : ```Linux ubuntu-16gb-fsn1-1 5.4.0-189-generic #209-Ubuntu SMP Fri Jun 7 14:05:13 UTC 2024 x86_64 x86_64 x86_64 GNU/Linux)```:**
- Path: `/usr/bin/certbot`
- Version: `certbot 2.9.0`
- Plugins list includes `nginx` (plus `apache`, `standalone`, `webroot`, etc.)

> If the `nginx` plugin appears here, you effectively have `python3-certbot-nginx` (or equivalent) installed and working.

---

## 2) (If needed) Ensure required system packages are present

> If step 1 already shows the nginx plugin, you don’t need to reinstall anything. For reference:

```bash
sudo apt-get update
sudo apt-get install -y nginx certbot python3-certbot-nginx
```

---

## 3) Firewall checks (no changes made)

Most Ubuntu hosts use UFW. These commands **only read** configuration:

```bash
sudo ufw status verbose
sudo ufw app list
sudo ufw app info 'Nginx Full'
```

**What you want to see:**
- UFW **Status: active**
- Rules allowing **80/tcp** and **443/tcp** (the profile **Nginx Full** covers both)

> If UFW is **inactive**, you might be using cloud firewalls (AWS SGs, GCP FW, etc.). Don’t enable UFW if it wasn’t already in use.

**If you do need to open ports (optional):**
```bash
sudo ufw allow 'Nginx Full'
```

---

## 4) Confirm Nginx is healthy and listening (read-only checks)

```bash
# Are ports 80/443 listening?
sudo ss -ltnp '( sport = :80 or sport = :443 )'

# Nginx service status
sudo systemctl status nginx --no-pager

# Validate Nginx config syntax
sudo nginx -t
```

> `nginx -t` does not reload; it just validates config. Safe to run.

---

## 5) Non-disruptive TLS checks

```bash
# See existing certs (if any)
sudo ls -l /etc/letsencrypt/live

# Dry-run renewal (uses staging; does not touch live certs)
sudo certbot renew --dry-run
```

---

## 6) Notes for a multi-site server (so you don’t break the other site)

- Create a **new** server block file for your test subdomain (do **not** edit the existing site file).
- After any change, always:
  ```bash
  sudo nginx -t        # validate
  sudo systemctl reload nginx   # reload (no downtime), not restart
  ```
- When you’re ready to issue a cert for the new subdomain (DNS pointed to this host), you can use the nginx plugin:
  ```bash
  sudo certbot --nginx -d subdomain.example.com
  ```
  Certbot will update the matching server block and reload Nginx for you.

---

## Summary

- Certbot is the **apt** build at `/usr/bin/certbot` (e.g., version **2.9.0**).
- The **nginx plugin is present and working**.
- UFW should allow **80/443** (or equivalent allowances in another firewall layer).
- Use `nginx -t` and `systemctl reload nginx` to avoid downtime.
