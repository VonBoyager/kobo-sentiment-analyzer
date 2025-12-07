#!/bin/bash
# Cleanup script for Digital Ocean Droplet
# Run this script to free up disk space

echo "=== Digital Ocean Droplet Cleanup Script ==="
echo ""

# Check current disk usage
echo "Current disk usage:"
df -h /
echo ""

# 1. Clean Docker system (can free 3-8 GB)
echo "1. Cleaning Docker system..."
docker system prune -a --volumes -f
echo "Docker cleanup complete."
echo ""

# 2. Clean Docker build cache
echo "2. Cleaning Docker build cache..."
docker builder prune -a -f
echo "Build cache cleanup complete."
echo ""

# 3. Remove unused Docker images
echo "3. Removing unused Docker images..."
docker image prune -a -f
echo "Image cleanup complete."
echo ""

# 4. Clean apt cache
echo "4. Cleaning apt cache..."
sudo apt-get clean
sudo apt-get autoremove -y
echo "Apt cleanup complete."
echo ""

# 5. Clean system logs (keep last 7 days)
echo "5. Cleaning old system logs..."
sudo journalctl --vacuum-time=7d
sudo find /var/log -type f -name "*.log" -mtime +7 -exec truncate -s 0 {} \;
echo "Log cleanup complete."
echo ""

# 6. Clean application logs (if they're large)
echo "6. Checking application logs..."
if [ -d "./logs" ]; then
    LOG_SIZE=$(du -sh ./logs | cut -f1)
    echo "Current log size: $LOG_SIZE"
    # Truncate large log files (>100MB)
    find ./logs -type f -size +100M -exec truncate -s 0 {} \;
    echo "Large log files truncated."
fi
echo ""

# 7. Clean Docker container logs
echo "7. Cleaning Docker container logs..."
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log 2>/dev/null || true
echo "Docker logs cleaned."
echo ""

# 8. Show Docker disk usage
echo "8. Docker disk usage after cleanup:"
docker system df
echo ""

# 9. Show largest directories
echo "9. Top 10 largest directories:"
du -h --max-depth=1 / 2>/dev/null | sort -hr | head -10
echo ""

# Final disk usage
echo "Final disk usage:"
df -h /
echo ""

echo "=== Cleanup Complete ==="
echo ""
echo "To check what's using space, run:"
echo "  du -h --max-depth=1 / | sort -hr | head -20"
echo ""
echo "To check Docker usage:"
echo "  docker system df"

