# 🚀 TaskFarmm Setup & Production Deployment Guide

This guide covers local environment setup, configuration parameters, and step-by-step production deployment instructions for **TaskFarmm**.

---

## 💻 1. Local Development Setup

### System Prerequisites
- **Python**: 3.11+
- **Git**: 2.30+
- **Pip**: 23.0+

### Step-by-Step Installation

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/logicbyroshan/taskfarmm-tasks-management.git
   cd taskfarmm-tasks-management
   ```

2. **Create & Activate Virtual Environment**:
   - **Windows (PowerShell)**:
     ```powershell
     python -m venv venv
     .\venv\Scripts\Activate.ps1
     ```
   - **macOS / Linux**:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```

3. **Install Required Packages**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize Environment Variables**:
   ```bash
   cp .env.example .env
   ```

5. **Apply Database Migrations**:
   ```bash
   python manage.py migrate
   ```

6. **Create an Admin Account**:
   ```bash
   python manage.py createsuperuser
   ```

7. **Launch the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Navigate to [http://127.0.0.1:8000/](http://127.0.0.1:8000/).

---

## 🚢 2. Cloud Platform Deployment

### Deploying to Render

1. Create a new **Web Service** on [Render](https://render.com/).
2. Connect your GitHub repository.
3. Configure the service:
   - **Environment**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt && python manage.py migrate && python manage.py collectstatic --noinput
     ```
   - **Start Command**:
     ```bash
     gunicorn config.wsgi --log-file -
     ```
4. Add Environment Variables:
   - `SECRET_KEY`: `<generate-a-strong-random-key>`
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `<your-render-app-subdomain>.onrender.com`

---

### Deploying to Railway

1. Click **New Project** → **Deploy from GitHub repo** on [Railway](https://railway.app/).
2. Railway will automatically detect the `Procfile` and `requirements.txt`.
3. Under **Variables**, add:
   - `SECRET_KEY`: `<random-secret-key>`
   - `DEBUG`: `False`
   - `ALLOWED_HOSTS`: `*`
4. Add a PostgreSQL database service (optional) and connect via `DATABASE_URL`.

---

## 🐧 3. Production VPS Deployment (Ubuntu 22.04 / 24.04 + Nginx + Gunicorn + Systemd)

### 1. System Package Setup
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install python3-pip python3-venv nginx git ufw -y
```

### 2. Project Directory & Permissions
```bash
sudo mkdir -p /var/www/taskfarmm
sudo chown -R $USER:$USER /var/www/taskfarmm
cd /var/www/taskfarmm
git clone https://github.com/logicbyroshan/taskfarmm-tasks-management.git .
```

### 3. Environment & Dependencies
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
nano .env  # Configure SECRET_KEY, DEBUG=False, ALLOWED_HOSTS=yourdomain.com
python manage.py migrate
python manage.py collectstatic --noinput
```

### 4. Configure Gunicorn Systemd Service
Create service file `/etc/systemd/system/taskfarmm.service`:
```ini
[Unit]
Description=TaskFarmm Gunicorn Daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/taskfarmm
ExecStart=/var/www/taskfarmm/venv/bin/gunicorn --access-logfile - --workers 3 --bind unix:/var/www/taskfarmm/taskfarmm.sock config.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl start taskfarmm
sudo systemctl enable taskfarmm
```

### 5. Configure Nginx Reverse Proxy
Create `/etc/nginx/sites-available/taskfarmm`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }

    location /static/ {
        alias /var/www/taskfarmm/staticfiles/;
    }

    location /media/ {
        alias /var/www/taskfarmm/media/;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/taskfarmm/taskfarmm.sock;
    }
}
```

Enable site and restart Nginx:
```bash
sudo ln -s /etc/nginx/sites-available/taskfarmm /etc/nginx/sites-enabled
sudo nginx -t
sudo systemctl restart nginx
```

### 6. Enable Free SSL (Let's Encrypt / Certbot)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

## 🔒 4. Production Security Checklist

- [x] **`DEBUG = False`** in `.env`
- [x] **Unique, randomized `SECRET_KEY`**
- [x] **`ALLOWED_HOSTS`** explicitly defined with your domain
- [x] **WhiteNoise enabled** for cached, compressed static files
- [x] **HTTPS/SSL** certificate active
- [x] **CSRF cookies and Session cookies secure**
