# 🌊 Digital Ocean Deployment Guide for Kobo Sentiment Analyzer

This guide covers deploying the Kobo Sentiment Analyzer application to Digital Ocean using Docker.

## 📋 Prerequisites

### Digital Ocean Account Setup
1. **Create Digital Ocean Account**: [Sign up](https://cloud.digitalocean.com/registrations/new)
2. **Create API Token**: Go to API → Personal Access Tokens → Generate New Token
3. **Create SSH Key**: Add your SSH public key to Digital Ocean

### Droplet Requirements
- **Minimum**: 2GB RAM, 1 CPU, 25GB SSD ($12/month)
- **Recommended**: 4GB RAM, 2 CPU, 50GB SSD ($24/month)
- **OS**: Ubuntu 20.04 LTS or 22.04 LTS
- **Region**: Choose closest to your users

## 🚀 Quick Start

### 1. Create Digital Ocean Droplet

#### Option A: Using Digital Ocean Control Panel
1. Go to **Droplets** → **Create Droplet**
2. Choose **Ubuntu 22.04 LTS**
3. Select **Basic Plan** with recommended specs
4. Add your SSH key
5. Choose a datacenter region
6. Give it a hostname (e.g., `kobo-sentiment-analyzer`)
7. Click **Create Droplet**

#### Option B: Using Digital Ocean CLI (doctl)
```bash
# Install doctl
snap install doctl

# Authenticate
doctl auth init

# Create droplet
doctl compute droplet create kobo-sentiment-analyzer \
  --image ubuntu-22-04-x64 \
  --size s-2vcpu-4gb \
  --region nyc1 \
  --ssh-keys YOUR_SSH_KEY_ID
```

### 2. Connect to Your Droplet
```bash
ssh root@YOUR_DROPLET_IP
```

### 3. Initial Server Setup
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

# Install Python and pip
apt install -y python3 python3-pip

# Install Git
apt install -y git

# Install Nginx (for reverse proxy)
apt install -y nginx

# Install UFW firewall
apt install -y ufw
```

### 4. Clone Your Repository
```bash
# Clone your repository
git clone https://github.com/yourusername/kobo-sentiment-analyzer.git
cd kobo-sentiment-analyzer

# Or upload your code using SCP
# scp -r /path/to/local/kobo root@YOUR_DROPLET_IP:/root/
```

### 5. Configure Environment
```bash
# Copy Digital Ocean environment template
cp env.digitalocean .env

# Edit with your settings
nano .env
```

**Required .env Configuration:**
```bash
# Replace with your actual values
SECRET_KEY=your-super-secret-key-here
ALLOWED_HOSTS=YOUR_DROPLET_IP,your-domain.com,www.your-domain.com
DB_PASSWORD=your-secure-database-password
```

### 6. Deploy Application
```bash
# Make deployment script executable
chmod +x deploy_digitalocean.py

# Deploy application
python3 deploy_digitalocean.py deploy

# Or with domain for SSL
python3 deploy_digitalocean.py deploy --domain your-domain.com
```

## 🔧 Detailed Configuration

### 1. Database Configuration
The application uses PostgreSQL in Docker. No additional setup needed.

### 2. Redis Configuration
Redis is also containerized. No additional setup needed.

### 3. Nginx Configuration
The deployment script automatically configures Nginx as a reverse proxy.

### 4. SSL/HTTPS Setup
If you provide a domain name, the script will automatically:
- Install Certbot
- Configure Let's Encrypt SSL
- Set up automatic renewal

### 5. Firewall Configuration
The script automatically configures UFW to allow:
- SSH (port 22)
- HTTP (port 80)
- HTTPS (port 443)

## 📊 Monitoring and Maintenance

### 1. Check Application Status
```bash
# Check Docker containers
docker-compose ps

# Check application logs
python3 deploy_digitalocean.py logs

# Check health
python3 deploy_digitalocean.py health
```

### 2. Application Management
```bash
# Start services
python3 deploy_digitalocean.py start

# Stop services
python3 deploy_digitalocean.py stop

# Restart services
python3 deploy_digitalocean.py restart

# View logs
python3 deploy_digitalocean.py logs
```

### 3. Database Management
```bash
# Access database
docker-compose exec db psql -U postgres -d sentiment_analyzer

# Backup database
docker-compose exec db pg_dump -U postgres sentiment_analyzer > backup.sql

# Restore database
docker-compose exec -T db psql -U postgres sentiment_analyzer < backup.sql
```

### 4. Log Management
```bash
# View application logs
tail -f logs/django.log

# View Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# View Docker logs
docker-compose logs -f web
```

## 🔄 Updates and Maintenance

### 1. Application Updates
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
python3 deploy_digitalocean.py build
python3 deploy_digitalocean.py restart
```

### 2. System Updates
```bash
# Update system packages
apt update && apt upgrade -y

# Restart services if needed
systemctl restart docker
```

### 3. SSL Certificate Renewal
```bash
# Test renewal
certbot renew --dry-run

# Manual renewal
certbot renew
```

## 🚨 Troubleshooting

### Common Issues

1. **Application Won't Start**
   ```bash
   # Check logs
   docker-compose logs web
   
   # Check environment variables
   cat .env
   
   # Restart services
   docker-compose restart
   ```

2. **Database Connection Issues**
   ```bash
   # Check database container
   docker-compose ps db
   
   # Check database logs
   docker-compose logs db
   
   # Restart database
   docker-compose restart db
   ```

3. **Static Files Not Loading**
   ```bash
   # Collect static files
   docker-compose exec web python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production
   
   # Check Nginx configuration
   nginx -t
   systemctl reload nginx
   ```

4. **SSL Certificate Issues**
   ```bash
   # Check certificate status
   certbot certificates
   
   # Renew certificate
   certbot renew --force-renewal
   ```

### Debug Commands
```bash
# Check system resources
htop
df -h
free -h

# Check network connectivity
netstat -tlnp
ss -tlnp

# Check Docker status
docker system df
docker system prune
```

## 📈 Scaling

### 1. Vertical Scaling
- Upgrade droplet size in Digital Ocean control panel
- Restart services after upgrade

### 2. Horizontal Scaling
- Use Digital Ocean Load Balancer
- Deploy multiple droplets
- Use managed databases (Digital Ocean Managed PostgreSQL)

### 3. Performance Optimization
- Enable Redis caching
- Use CDN for static files
- Optimize database queries
- Monitor resource usage

## 💰 Cost Optimization

### 1. Right-size Your Droplet
- Start with minimum requirements
- Monitor usage and scale up as needed
- Use Digital Ocean monitoring

### 2. Use Managed Services
- Digital Ocean Managed PostgreSQL
- Digital Ocean Spaces (S3-compatible storage)
- Digital Ocean Load Balancer

### 3. Backup Strategy
- Regular database backups
- Snapshot your droplet
- Use Digital Ocean Spaces for backups

## 🔐 Security Best Practices

1. **Keep System Updated**
   ```bash
   apt update && apt upgrade -y
   ```

2. **Configure Firewall**
   ```bash
   ufw status
   ufw enable
   ```

3. **Use Strong Passwords**
   - Database passwords
   - Django secret key
   - SSH keys

4. **Regular Backups**
   - Database backups
   - Application code backups
   - Configuration backups

5. **Monitor Logs**
   - Application logs
   - System logs
   - Security logs

## 📞 Support

### Digital Ocean Support
- **Documentation**: [Digital Ocean Docs](https://docs.digitalocean.com/)
- **Community**: [Digital Ocean Community](https://www.digitalocean.com/community)
- **Support**: [Digital Ocean Support](https://cloud.digitalocean.com/support)

### Application Support
- **Health Check**: `http://YOUR_DROPLET_IP/api/health/`
- **Admin Panel**: `http://YOUR_DROPLET_IP/admin/`
- **API Documentation**: `http://YOUR_DROPLET_IP/api/`

---

**Note**: This deployment guide should be customized based on your specific Digital Ocean setup and requirements. Always test deployments in a staging environment before production.
