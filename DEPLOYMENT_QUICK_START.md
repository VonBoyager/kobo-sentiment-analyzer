# 🚀 Quick Start: Digital Ocean Deployment

## Prerequisites
- Digital Ocean account
- Droplet created (Ubuntu 22.04 LTS, 2GB+ RAM)
- Domain name (optional, for SSL)

## Quick Deployment (5 Steps)

### 1. Connect to Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### 2. Install Dependencies
```bash
apt update && apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt install -y nodejs git nginx ufw
```

### 3. Clone & Configure
```bash
git clone https://github.com/VonBoyager/kobo-sentiment-analyzer.git
cd kobo-sentiment-analyzer
cp env.digitalocean .env
nano .env  # Update SECRET_KEY, ALLOWED_HOSTS, DB_PASSWORD
```

### 4. Deploy
```bash
chmod +x deploy_digitalocean.py
python3 deploy_digitalocean.py deploy
# Or with domain: python3 deploy_digitalocean.py deploy --domain your-domain.com
```

### 5. Create Admin User
```bash
docker-compose exec web python manage.py createsuperuser --settings=sentiment_analyzer.settings_production
```

## Access Your Application
- **Frontend**: `http://YOUR_DROPLET_IP` or `https://your-domain.com`
- **Admin Panel**: `http://YOUR_DROPLET_IP/admin/`
- **API**: `http://YOUR_DROPLET_IP/api/`

## Next Steps
1. Upload CSV data via `/upload` page
2. Train ML models via Dashboard "Test Models" button
3. View analytics in Dashboard and Results pages

## Troubleshooting
- **Check logs**: `docker-compose logs -f web`
- **Health check**: `curl http://localhost/api/health/`
- **Restart**: `docker-compose restart`

For detailed instructions, see [DEPLOYMENT_CHECKLIST.md](./DEPLOYMENT_CHECKLIST.md)

