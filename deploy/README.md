# Deploy Midnight on Ubuntu 24.04 — teamcafe.cloud

Paths assume the app lives at `/srv/midnight`. Adjust if you use another directory.

## 1. DNS

At your registrar, point **A** records for `teamcafe.cloud` and `www.teamcafe.cloud` to your VPS **public IPv4**.

## 2. Packages

```bash
sudo apt update
sudo apt install -y python3-venv python3-dev nginx postgresql postgresql-contrib certbot python3-certbot-nginx git
```

## 3. Code and venv

```bash
sudo mkdir -p /srv/midnight
sudo chown $USER:$USER /srv/midnight
cd /srv/midnight
# clone or upload your project so manage.py is here
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 4. PostgreSQL

```bash
sudo -u postgres psql -c "CREATE USER midnight WITH PASSWORD 'YOUR_STRONG_PASSWORD';"
sudo -u postgres psql -c "CREATE DATABASE midnight OWNER midnight;"
```

## 5. Environment

```bash
cp deploy/teamcafe.env.example /srv/midnight/.env
chmod 600 /srv/midnight/.env
nano /srv/midnight/.env
```

Set `DJANGO_SECRET_KEY` (long random string), `DB_PASSWORD`, and any other placeholders.

## 6. Django

```bash
cd /srv/midnight
source .venv/bin/activate
python manage.py migrate
python manage.py collectstatic --noinput
```

## 7. Permissions for www-data

```bash
sudo chown -R www-data:www-data /srv/midnight
```

(Ensure your login user can still `git pull` if needed, or use a dedicated deploy user and group.)

## 8. Gunicorn (systemd)

```bash
sudo cp deploy/midnight.service /etc/systemd/system/midnight.service
sudo systemctl daemon-reload
sudo systemctl enable --now midnight
sudo systemctl status midnight
```

## 9. Nginx

```bash
sudo cp deploy/nginx-teamcafe.cloud.conf /etc/nginx/sites-available/midnight
sudo ln -sf /etc/nginx/sites-available/midnight /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## 10. HTTPS

```bash
sudo certbot --nginx -d teamcafe.cloud -d www.teamcafe.cloud
```

Follow the prompts. Certbot will update Nginx for TLS.

## 11. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## 12. Create superuser (optional)

```bash
sudo -u www-data bash -c 'cd /srv/midnight && source .venv/bin/activate && set -a && source .env && set +a && python manage.py createsuperuser'
```

After deploys: `sudo systemctl restart midnight` and `python manage.py migrate` as needed.
