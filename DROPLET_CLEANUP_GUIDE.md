# Digital Ocean Droplet Cleanup Guide

## Why Your Droplet Uses 20GB Instead of 4.5GB

Your application code is ~4.5GB, but a Digital Ocean droplet includes:

### Typical Breakdown (20GB Total)

| Component | Size | Notes |
|-----------|------|-------|
| **Operating System (Ubuntu)** | 2-4 GB | Base system |
| **Docker System** | 1-2 GB | Docker daemon, images |
| **Docker Build Cache** | 2-5 GB | **Largest culprit - accumulates over time** |
| **Docker Images (all versions)** | 1-2 GB | Old/unused images |
| **Application Code** | 0.5-1 GB | Your code + dependencies |
| **Media/ML Models** | 3.9 GB | Your ML models |
| **PostgreSQL Data** | 1-5 GB | Grows with usage |
| **Logs (all services)** | 1-5 GB | **Major culprit - no rotation** |
| **System Cache** | 0.5-1 GB | apt cache, temp files |
| **TOTAL** | **~12-24 GB** | Can easily reach 20GB |

## Quick Fix: Run Cleanup Script

I've created a cleanup script for you. On your droplet, run:

```bash
cd ~/kobo-sentiment-analyzer-master
chmod +x cleanup_droplet.sh
./cleanup_droplet.sh
```

This will free up **5-10 GB** typically.

## Manual Cleanup Commands

### 1. Clean Docker (Frees 3-8 GB)

```bash
# Clean everything unused
docker system prune -a --volumes

# Clean build cache specifically
docker builder prune -a

# Remove unused images
docker image prune -a
```

### 2. Check What's Using Space

```bash
# Overall disk usage
df -h

# Docker usage
docker system df

# Largest directories
du -h --max-depth=1 / | sort -hr | head -20

# Check log sizes
du -sh /var/log/*
du -sh ./logs/*
```

### 3. Clean Logs (Frees 1-5 GB)

```bash
# System logs (keep last 7 days)
sudo journalctl --vacuum-time=7d

# Application logs
find ./logs -type f -size +100M -exec truncate -s 0 {} \;

# Docker container logs
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log
```

### 4. Clean System Cache

```bash
sudo apt-get clean
sudo apt-get autoremove -y
```

## Permanent Fix: Add Log Rotation

I've updated `docker-compose.yml` to include log rotation. After pulling the changes:

```bash
# Pull latest changes
git pull

# Restart services with new log rotation
docker-compose down
docker-compose up -d
```

This will limit logs to:
- Max 10MB per log file
- Keep only 3 log files per service
- Prevents logs from growing indefinitely

## Check Database Size

```bash
# Check PostgreSQL database size
docker-compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('sentiment_analyzer'));"

# Vacuum database to reclaim space
docker-compose exec db psql -U postgres -d sentiment_analyzer -c "VACUUM FULL;"
```

## Expected Size After Cleanup

After running cleanup:
- **Operating System**: 2-4 GB
- **Docker System**: 500 MB - 1 GB
- **Application**: 500 MB - 1 GB
- **Media/ML Models**: 3.9 GB
- **Database**: 1-2 GB
- **Logs**: 100-500 MB (with rotation)
- **Total**: **~8-12 GB** (reasonable)

## Prevention: Regular Maintenance

Add to crontab for weekly cleanup:

```bash
# Edit crontab
crontab -e

# Add this line (runs every Sunday at 2 AM)
0 2 * * 0 cd ~/kobo-sentiment-analyzer-master && ./cleanup_droplet.sh >> /var/log/cleanup.log 2>&1
```

## Most Common Issues

1. **Docker Build Cache (2-5 GB)**: Clean with `docker builder prune -a`
2. **Log Files (1-5 GB)**: Now fixed with log rotation in docker-compose.yml
3. **Old Docker Images (1-2 GB)**: Clean with `docker image prune -a`
4. **PostgreSQL Bloat (1-3 GB)**: Run `VACUUM FULL` periodically

## Quick Diagnostic Commands

Run these to see what's using space:

```bash
# Top 10 largest directories
du -h --max-depth=1 / 2>/dev/null | sort -hr | head -10

# Docker disk usage
docker system df -v

# Check specific directories
du -sh /var/lib/docker/*
du -sh ./logs/*
du -sh ./media/*
```

After cleanup, your droplet should be around **8-12 GB**, which is normal for a production server with your application.

