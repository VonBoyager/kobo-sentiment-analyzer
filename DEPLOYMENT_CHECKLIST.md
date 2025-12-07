# 🚀 Digital Ocean Deployment Checklist

This checklist will guide you through deploying the Kobo Sentiment Analyzer to Digital Ocean.

## Pre-Deployment Checklist

### 1. Environment Variables
- [ ] Copy `env.digitalocean` to `.env` on the server
- [ ] Update `SECRET_KEY` with a strong, unique key
- [ ] Update `ALLOWED_HOSTS` with your droplet IP and domain (if applicable)
- [ ] Update `DB_PASSWORD` with a secure password
- [ ] Configure email settings if needed
- [ ] Set `DEBUG=False` for production

### 2. Digital Ocean Droplet Setup
- [ ] Create a droplet (minimum 2GB RAM, 1 CPU recommended)
- [ ] Choose Ubuntu 22.04 LTS
- [ ] Add your SSH key
- [ ] Note your droplet IP address
- [ ] Configure firewall (ports 22, 80, 443)

### 3. Domain Configuration (Optional)
- [ ] Point your domain to the droplet IP
- [ ] Update DNS records (A record)
- [ ] Wait for DNS propagation

## Deployment Steps

### Step 1: Connect to Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### Step 2: Install Prerequisites
```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Install Node.js (for frontend build)
curl -fsSL https://deb.nodesource.com/setup_18.x | bash -
apt install -y nodejs

# Install Git
apt install -y git

# Install Nginx (for reverse proxy)
apt install -y nginx

# Install UFW firewall
apt install -y ufw
```

### Step 3: Clone Repository
```bash
git clone https://github.com/VonBoyager/kobo-sentiment-analyzer.git
cd kobo-sentiment-analyzer
```

### Step 4: Configure Environment
```bash
# Copy environment template
cp env.digitalocean .env

# Edit with your settings
nano .env
```

**Required changes in `.env`:**
- `SECRET_KEY`: Generate a new secret key
- `ALLOWED_HOSTS`: Add your droplet IP and domain
- `DB_PASSWORD`: Set a secure password
- `DEBUG=False`

### Step 5: Setup Firewall
```bash
ufw allow ssh
ufw allow 80
ufw allow 443
ufw --force enable
```

### Step 6: Deploy Application
```bash
# Make deployment script executable
chmod +x deploy_digitalocean.py

# Deploy (without domain)
python3 deploy_digitalocean.py deploy

# Or with domain for SSL
python3 deploy_digitalocean.py deploy --domain your-domain.com
```

### Step 7: Verify Deployment
```bash
# Check container status
docker-compose ps

# Check application health
python3 deploy_digitalocean.py health

# View logs if needed
python3 deploy_digitalocean.py logs
```

## Post-Deployment Tasks

### 1. Create Superuser
```bash
docker-compose exec web python manage.py createsuperuser --settings=sentiment_analyzer.settings_production
```

### 2. Load Initial Data (Optional)
```bash
# Upload CSV file through the web interface at /upload
# Or use management command:
docker-compose exec web python manage.py load_dataset --username admin --file /path/to/data.csv --settings=sentiment_analyzer.settings_production
```

### 3. Train ML Models
- Access the Dashboard at `http://YOUR_DROPLET_IP/dashboard`
- Click "Test Models" button in the "ML Ready" card
- Wait for training to complete (this may take several minutes)

### 4. SSL Certificate (If using domain)
The deployment script should automatically configure SSL if you provided a domain. If not:

```bash
# Install Certbot
apt install -y certbot python3-certbot-nginx

# Obtain certificate
certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Monitoring and Maintenance

### Check Application Status
```bash
# Container status
docker-compose ps

# Application logs
docker-compose logs -f web

# Health check
curl http://localhost/api/health/
```

### Database Backup
```bash
# Create backup
docker-compose exec db pg_dump -U postgres sentiment_analyzer > backup_$(date +%Y%m%d).sql

# Restore backup
docker-compose exec -T db psql -U postgres sentiment_analyzer < backup_20250101.sql
```

### Update Application
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
python3 deploy_digitalocean.py build
python3 deploy_digitalocean.py restart
```

## Troubleshooting

### Application Won't Start
1. Check logs: `docker-compose logs web`
2. Verify environment variables: `cat .env`
3. Check database connection: `docker-compose exec db psql -U postgres -d sentiment_analyzer`
4. Restart services: `docker-compose restart`

### Database Connection Issues
1. Check database container: `docker-compose ps db`
2. Check database logs: `docker-compose logs db`
3. Verify credentials in `.env`
4. Restart database: `docker-compose restart db`

### Static Files Not Loading
1. Collect static files:
   ```bash
   docker-compose exec web python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production
   ```
2. Check Nginx configuration: `nginx -t`
3. Reload Nginx: `systemctl reload nginx`

### SSL Certificate Issues
1. Check certificate status: `certbot certificates`
2. Renew certificate: `certbot renew --force-renewal`
3. Check Nginx SSL configuration

## Security Checklist

- [ ] Changed default `SECRET_KEY`
- [ ] Set `DEBUG=False`
- [ ] Configured `ALLOWED_HOSTS`
- [ ] Set strong `DB_PASSWORD`
- [ ] Enabled firewall (UFW)
- [ ] SSL certificate installed (if using domain)
- [ ] Regular backups scheduled
- [ ] System updates applied
- [ ] SSH key authentication enabled
- [ ] Disabled password authentication for SSH

## Performance Optimization

1. **Enable Redis Caching**: Already configured in docker-compose.yml
2. **CDN for Static Files**: Consider using Digital Ocean Spaces
3. **Database Optimization**: Monitor query performance
4. **Resource Monitoring**: Use Digital Ocean monitoring tools

## Support Resources

- **Digital Ocean Docs**: https://docs.digitalocean.com/
- **Docker Docs**: https://docs.docker.com/
- **Django Deployment**: https://docs.djangoproject.com/en/stable/howto/deployment/
- **Project Repository**: https://github.com/VonBoyager/kobo-sentiment-analyzer

---

**Note**: Always test deployments in a staging environment before production!

