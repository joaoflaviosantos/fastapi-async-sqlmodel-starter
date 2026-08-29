# Deploy — Native (Linux VPS)

Use this when you want to deploy the application **directly on a Linux VPS** without Docker, using Nginx as a reverse proxy and Supervisor to manage processes.

Based on the guide: [FastAPI with Nginx and Gunicorn](https://dylancastillo.co/posts/fastapi-nginx-gunicorn.html) by Dylan Castillo.

## Directory structure

```
native/
├── logs/           # Log output directory (must exist before starting services)
├── nginx/
│   └── nginx.conf  # Nginx reverse-proxy configuration
├── scripts/        # Bash wrapper scripts that launch each process
│   ├── backend-api
│   ├── backend-worker
│   └── backend-scheduler
└── supervisor/     # Supervisor program configurations
    ├── backend-api.conf
    ├── backend-worker.conf
    └── backend-scheduler.conf
```

## Setup

> All paths below assume the project is cloned to `/home/ubuntu/fastapi-async-sqlmodel-starter`. Adjust them to match your server.

### 1. Install dependencies

```bash
sudo apt update
sudo apt install nginx supervisor python3-pip python3-venv
```

### 2. Set up the virtual environment and install Python dependencies

```bash
cd /home/ubuntu/fastapi-async-sqlmodel-starter/backend
python3 -m venv .venv
source .venv/bin/activate
pip install poetry==1.7.1
poetry install --no-root
```

### 3. Configure environment variables

Copy `backend/.env.example` to `backend/.env` and fill in your production values:

```bash
cp backend/.env.example backend/.env
nano backend/.env
```

### 4. Run database migrations

```bash
cd backend
source .venv/bin/activate
alembic upgrade head
```

### 5. Make the scripts executable

```bash
chmod +x deploy/native/scripts/backend-api
chmod +x deploy/native/scripts/backend-worker
chmod +x deploy/native/scripts/backend-scheduler
```

### 6. Link Supervisor configs

```bash
sudo ln -sf /home/ubuntu/fastapi-async-sqlmodel-starter/deploy/native/supervisor/backend-api.conf /etc/supervisor/conf.d/backend-api.conf
sudo ln -sf /home/ubuntu/fastapi-async-sqlmodel-starter/deploy/native/supervisor/backend-worker.conf /etc/supervisor/conf.d/backend-worker.conf
sudo ln -sf /home/ubuntu/fastapi-async-sqlmodel-starter/deploy/native/supervisor/backend-scheduler.conf /etc/supervisor/conf.d/backend-scheduler.conf

sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start all
```

### 7. Link Nginx config

> [!IMPORTANT]
> You must disable the default Nginx site, otherwise your domain will continue to serve the Nginx welcome page instead of the application.

```bash
sudo ln -sf /home/ubuntu/fastapi-async-sqlmodel-starter/deploy/native/nginx/nginx.conf /etc/nginx/sites-enabled/fastapi-app
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl reload nginx
```

## Useful Supervisor commands

```bash
sudo supervisorctl status          # View all process statuses
sudo supervisorctl restart all     # Restart all processes
sudo supervisorctl tail backend-api stdout  # Stream API logs
```
