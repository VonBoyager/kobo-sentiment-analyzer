# Digital Ocean Droplet Size Diagnosis

## Why 20GB Instead of ~4.5GB?

The application itself is ~4.5GB, but a Digital Ocean droplet includes much more than just the application. Here's what typically consumes space:

## Common Space Consumers on a Droplet

### 1. Operating System
- **Ubuntu/Debian base system**: ~2-4 GB
- **System packages**: ~500 MB - 1 GB
- **Kernel and drivers**: ~200-500 MB

### 2. Docker System
- **Docker daemon and tools**: ~200-300 MB
- **Docker images** (can be large):
  - Python base image: ~150-200 MB
  - Node.js base image: ~150-200 MB (if used)
  - PostgreSQL image: ~200-250 MB
  - Redis image: ~50-100 MB
  - Nginx image: ~25-50 MB
  - **Total base images**: ~575-800 MB
- **Docker build cache**: Can be 2-5 GB (accumulates over time)
- **Unused/old Docker images**: Can be several GB
- **Docker volumes**: Variable, but can grow large

### 3. Application Data
- **PostgreSQL data**: Can grow to several GB with data
- **Redis data**: Usually small (~100-500 MB)
- **Application logs**: Can grow to 1-5 GB if not rotated
- **Nginx logs**: Can grow to several GB
- **Media files**: 3.9 GB (your ML models)
- **Static files**: ~3-4 MB

### 4. System Files
- **apt cache**: ~200-500 MB
- **System logs**: ~100-500 MB
- **Temporary files**: Variable
- **Swap files**: If configured, can be 1-4 GB

### 5. Docker Build Artifacts
- **Multi-stage build intermediate layers**: Can be 1-3 GB
- **Build cache**: 2-5 GB
- **Unused layers**: Can accumulate

## Typical Breakdown for Your Application

| Component | Estimated Size |
|-----------|----------------|
| Operating System (Ubuntu) | 2-4 GB |
| Docker System | 1-2 GB |
| Docker Images (all) | 1-2 GB |
| Docker Build Cache | 2-5 GB |
| Application Code & Dependencies | 0.5-1 GB |
| Media/ML Models | 3.9 GB |
| PostgreSQL Data | 1-5 GB (grows with usage) |
| Logs (all services) | 1-3 GB |
| System Cache & Temp | 0.5-1 GB |
| **TOTAL** | **~12-24 GB** |

## Commands to Diagnose on Your Droplet

Run these commands on your Digital Ocean droplet to see what's using space:

```bash
# Check overall disk usage
df -h

# Check Docker disk usage
docker system df

# Check Docker images
docker images

# Check Docker containers
docker ps -a

# Check largest directories
du -h --max-depth=1 / | sort -hr | head -20

# Check Docker volumes
docker volume ls
docker volume inspect <volume_name>

# Check log sizes
du -sh /var/log/*
du -sh /var/lib/docker/containers/*/

# Check PostgreSQL data size
sudo du -sh /var/lib/postgresql/*

# Check application logs
du -sh ~/kobo-sentiment-analyzer-master/logs/*
du -sh ~/kobo-sentiment-analyzer-master/media/*

# Check Docker build cache
docker builder du
```

## Common Issues and Solutions

### 1. Docker Build Cache (Most Common)
**Problem**: Docker accumulates build cache that can be several GB.

**Solution**:
```bash
# Clean Docker build cache
docker builder prune -a

# Clean all unused Docker resources
docker system prune -a --volumes
```

### 2. Old/Unused Docker Images
**Problem**: Old versions of images accumulate.

**Solution**:
```bash
# Remove unused images
docker image prune -a

# Remove specific old images
docker rmi <image_id>
```

### 3. Large Log Files
**Problem**: Application and system logs grow indefinitely.

**Solution**:
```bash
# Set up log rotation in docker-compose.yml
# Add logging configuration:
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"

# Clean existing large logs
sudo truncate -s 0 /var/log/*.log
docker-compose logs --tail=0 > /dev/null
```

### 4. PostgreSQL Data Growth
**Problem**: Database grows with data.

**Solution**:
```bash
# Check database size
docker-compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('sentiment_analyzer'));"

# Vacuum database to reclaim space
docker-compose exec db psql -U postgres -d sentiment_analyzer -c "VACUUM FULL;"
```

### 5. Media/ML Models
**Problem**: 3.9 GB of ML models in the repository.

**Solution**: Move to external storage (S3, Cloudflare R2) or separate volume.

## Recommended Actions

1. **Clean Docker system** (can free 3-8 GB):
   ```bash
   docker system prune -a --volumes
   ```

2. **Set up log rotation** in docker-compose.yml

3. **Move media files** to external storage

4. **Monitor disk usage** regularly:
   ```bash
   # Add to crontab for daily monitoring
   0 0 * * * df -h >> /var/log/disk_usage.log
   ```

5. **Use Docker multi-stage builds** (already implemented) to reduce image size

6. **Clean apt cache**:
   ```bash
   sudo apt-get clean
   sudo apt-get autoremove
   ```

## Expected Size After Cleanup

After proper cleanup:
- **Operating System**: 2-4 GB
- **Docker System**: 500 MB - 1 GB
- **Application**: 500 MB - 1 GB
- **Media/ML Models**: 3.9 GB (or external)
- **Database**: 1-2 GB (depends on data)
- **Logs**: 100-500 MB (with rotation)
- **Total**: ~8-12 GB (reasonable for a production server)

If you're still at 20GB after cleanup, check:
- Multiple Docker image versions
- Large log files
- Database bloat
- Unused Docker volumes
- System backups

