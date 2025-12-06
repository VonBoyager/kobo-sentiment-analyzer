# 🚀 Deployment Guide for Kobo Sentiment Analyzer

This guide covers deploying the Kobo Sentiment Analyzer application to production.

## 📋 Prerequisites

### System Requirements
- **OS**: Ubuntu 20.04+ / CentOS 8+ / RHEL 8+
- **RAM**: Minimum 4GB, Recommended 8GB+
- **Storage**: Minimum 20GB free space
- **CPU**: 2+ cores recommended

### Software Requirements
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **Python**: 3.8+ (if not using Docker)
- **Node.js**: 16+ (if not using Docker)
- **PostgreSQL**: 12+
- **Redis**: 6+

## 🏗️ Deployment Options

### Option 1: Docker Deployment (Recommended)

#### 1. Clone and Setup
```bash
git clone <your-repository>
cd Kobo
cp env.production .env
# Edit .env with your production settings
```

#### 2. Configure Environment
Edit `.env` file with your production settings:
```bash
# Required settings
SECRET_KEY=your-super-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DB_PASSWORD=your-secure-database-password
```

#### 3. Deploy with Docker
```bash
# Full deployment
python deploy.py deploy

# Or step by step
python deploy.py build
python deploy.py start
```

#### 4. Verify Deployment
```bash
# Check health
python deploy.py health

# View logs
python deploy.py logs
```

### Option 2: Manual Deployment

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install required packages
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib redis-server nginx

# Install Node.js
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs
```

#### 2. Database Setup
```bash
# Create database and user
sudo -u postgres psql
CREATE DATABASE sentiment_analyzer_prod;
CREATE USER sentiment_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE sentiment_analyzer_prod TO sentiment_user;
\q
```

#### 3. Application Setup
```bash
# Clone repository
git clone <your-repository>
cd Kobo

# Setup Python environment
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Setup frontend
cd frontend
npm install
npm run build
cd ..

# Configure environment
cp env.production .env
# Edit .env with your settings

# Run migrations
cd sentiment_analyzer
python manage.py migrate --settings=sentiment_analyzer.settings_production
python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production
python manage.py createsuperuser --settings=sentiment_analyzer.settings_production
```

#### 4. Configure Nginx
```bash
# Copy nginx configuration
sudo cp nginx.conf /etc/nginx/sites-available/sentiment-analyzer
sudo ln -s /etc/nginx/sites-available/sentiment-analyzer /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 5. Setup Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/sentiment-analyzer.service
```

Service file content:
```ini
[Unit]
Description=Kobo Sentiment Analyzer
After=network.target

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/path/to/Kobo/sentiment_analyzer
Environment=DJANGO_SETTINGS_MODULE=sentiment_analyzer.settings_production
ExecStart=/path/to/Kobo/venv/bin/gunicorn --bind 127.0.0.1:8000 --workers 3 sentiment_analyzer.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable sentiment-analyzer
sudo systemctl start sentiment-analyzer
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `SECRET_KEY` | Django secret key | Yes | - |
| `DEBUG` | Debug mode | Yes | False |
| `ALLOWED_HOSTS` | Allowed hosts | Yes | - |
| `DB_*` | Database settings | Yes | - |
| `REDIS_URL` | Redis URL | Yes | - |
| `EMAIL_*` | Email settings | No | Console backend |
| `AWS_*` | AWS S3 settings | No | - |
| `SENTRY_DSN` | Sentry DSN | No | - |

### Security Configuration

1. **SSL/TLS**: Configure SSL certificates
2. **Firewall**: Configure firewall rules
3. **Database**: Use strong passwords
4. **Secrets**: Store secrets securely

### Performance Tuning

1. **Database**: Configure PostgreSQL for production
2. **Redis**: Configure Redis for caching
3. **Nginx**: Configure Nginx for static files
4. **Gunicorn**: Adjust worker processes

## 📊 Monitoring

### Health Checks
```bash
# Check application health
python monitoring/health_check.py

# Check via API
curl http://your-domain.com/api/health/
```

### Logs
```bash
# Application logs
tail -f logs/django.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f
```

### Metrics
- **CPU Usage**: Monitor CPU utilization
- **Memory Usage**: Monitor RAM usage
- **Disk Space**: Monitor storage
- **Database**: Monitor query performance
- **API**: Monitor response times

## 💾 Backup and Recovery

### Automated Backups
```bash
# Create full backup
python backup/backup_manager.py backup-full

# Schedule backups (crontab)
0 2 * * * /path/to/Kobo/backup/backup_manager.py backup-full
```

### Manual Backups
```bash
# Database only
python backup/backup_manager.py backup-db

# Media files only
python backup/backup_manager.py backup-media

# ML models only
python backup/backup_manager.py backup-models
```

### Recovery
```bash
# Restore full backup
python backup/backup_manager.py restore-full --backup-name backup_20240101_120000

# Restore specific components
python backup/backup_manager.py restore-db --file backups/db_backup_20240101_120000.sql.gz
```

## 🔄 Updates and Maintenance

### Application Updates
```bash
# Pull latest changes
git pull origin main

# Update dependencies
pip install -r requirements.txt
cd frontend && npm install && npm run build

# Run migrations
python sentiment_analyzer/manage.py migrate --settings=sentiment_analyzer.settings_production

# Restart services
python deploy.py restart
```

### Database Maintenance
```bash
# Run database maintenance
sudo -u postgres psql sentiment_analyzer_prod -c "VACUUM ANALYZE;"

# Check database size
sudo -u postgres psql sentiment_analyzer_prod -c "SELECT pg_size_pretty(pg_database_size('sentiment_analyzer_prod'));"
```

### Cleanup
```bash
# Clean old backups
python backup/backup_manager.py cleanup --days 30

# Clean old logs
find logs/ -name "*.log" -mtime +30 -delete
```

## 🚨 Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Check database service status
   - Verify connection settings
   - Check firewall rules

2. **Static Files Not Loading**
   - Run `collectstatic`
   - Check Nginx configuration
   - Verify file permissions

3. **Memory Issues**
   - Increase server RAM
   - Optimize database queries
   - Configure swap space

4. **Performance Issues**
   - Enable caching
   - Optimize database
   - Use CDN for static files

### Debug Mode
```bash
# Enable debug mode temporarily
export DEBUG=True
python sentiment_analyzer/manage.py runserver --settings=sentiment_analyzer.settings
```

### Log Analysis
```bash
# Check error logs
grep ERROR logs/django.log

# Check slow queries
grep "slow query" logs/django.log

# Monitor real-time logs
tail -f logs/django.log | grep -E "(ERROR|WARNING)"
```

## 📞 Support

### Getting Help
1. Check logs for error messages
2. Run health checks
3. Review configuration
4. Check system resources

### Emergency Procedures
1. **Service Down**: Restart services
2. **Database Issues**: Restore from backup
3. **Security Breach**: Change passwords, review logs
4. **Performance Issues**: Scale resources

## 🔐 Security Checklist

- [ ] SSL/TLS certificates configured
- [ ] Firewall rules configured
- [ ] Strong passwords set
- [ ] Database access restricted
- [ ] File permissions set correctly
- [ ] Regular security updates
- [ ] Monitoring configured
- [ ] Backups tested
- [ ] Error logging enabled
- [ ] Rate limiting configured

## 📈 Scaling

### Horizontal Scaling
- Load balancer configuration
- Multiple application servers
- Database replication
- Redis clustering

### Vertical Scaling
- Increase server resources
- Optimize application code
- Database tuning
- Caching strategies

---

**Note**: This deployment guide should be customized based on your specific infrastructure and requirements. Always test deployments in a staging environment before production.
