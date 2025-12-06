#!/usr/bin/env python3
"""
Health check script for Kobo Sentiment Analyzer
"""

import os
import sys
import requests
import psycopg2
import redis
from pathlib import Path

# Add Django project to path
sys.path.append(str(Path(__file__).parent.parent / 'sentiment_analyzer'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sentiment_analyzer.settings_production')

import django
django.setup()

from django.conf import settings
from django.db import connection

class HealthChecker:
    def __init__(self):
        self.checks = []
        self.overall_status = True
    
    def add_check(self, name, status, message=""):
        """Add a health check result"""
        self.checks.append({
            'name': name,
            'status': status,
            'message': message
        })
        if not status:
            self.overall_status = False
    
    def check_database(self):
        """Check database connectivity"""
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                if result[0] == 1:
                    self.add_check("Database", True, "Database connection successful")
                else:
                    self.add_check("Database", False, "Database query failed")
        except Exception as e:
            self.add_check("Database", False, f"Database connection failed: {str(e)}")
    
    def check_redis(self):
        """Check Redis connectivity"""
        try:
            r = redis.from_url(settings.CACHES['default']['LOCATION'])
            r.ping()
            self.add_check("Redis", True, "Redis connection successful")
        except Exception as e:
            self.add_check("Redis", False, f"Redis connection failed: {str(e)}")
    
    def check_static_files(self):
        """Check if static files are accessible"""
        try:
            static_root = settings.STATIC_ROOT
            if static_root and Path(static_root).exists():
                self.add_check("Static Files", True, "Static files directory exists")
            else:
                self.add_check("Static Files", False, "Static files directory not found")
        except Exception as e:
            self.add_check("Static Files", False, f"Static files check failed: {str(e)}")
    
    def check_media_files(self):
        """Check if media files directory is writable"""
        try:
            media_root = settings.MEDIA_ROOT
            if media_root and Path(media_root).exists():
                # Check if directory is writable
                test_file = Path(media_root) / 'health_check.tmp'
                test_file.write_text('test')
                test_file.unlink()
                self.add_check("Media Files", True, "Media files directory is writable")
            else:
                self.add_check("Media Files", False, "Media files directory not found")
        except Exception as e:
            self.add_check("Media Files", False, f"Media files check failed: {str(e)}")
    
    def check_disk_space(self):
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage('/')
            free_gb = free // (1024**3)
            if free_gb > 1:  # At least 1GB free
                self.add_check("Disk Space", True, f"{free_gb}GB available")
            else:
                self.add_check("Disk Space", False, f"Only {free_gb}GB available")
        except Exception as e:
            self.add_check("Disk Space", False, f"Disk space check failed: {str(e)}")
    
    def check_memory(self):
        """Check available memory"""
        try:
            with open('/proc/meminfo', 'r') as f:
                meminfo = f.read()
            
            for line in meminfo.split('\n'):
                if 'MemAvailable' in line:
                    available_kb = int(line.split()[1])
                    available_gb = available_kb // (1024**2)
                    if available_gb > 0.5:  # At least 512MB available
                        self.add_check("Memory", True, f"{available_gb}GB available")
                    else:
                        self.add_check("Memory", False, f"Only {available_gb}GB available")
                    break
        except Exception as e:
            self.add_check("Memory", False, f"Memory check failed: {str(e)}")
    
    def check_api_endpoints(self):
        """Check if API endpoints are responding"""
        try:
            base_url = "http://localhost:8000"
            
            # Check health endpoint
            response = requests.get(f"{base_url}/api/health/", timeout=5)
            if response.status_code == 200:
                self.add_check("API Health", True, "Health endpoint responding")
            else:
                self.add_check("API Health", False, f"Health endpoint returned {response.status_code}")
            
            # Check admin endpoint
            response = requests.get(f"{base_url}/admin/", timeout=5)
            if response.status_code in [200, 302]:  # 302 is redirect to login
                self.add_check("Admin Interface", True, "Admin interface accessible")
            else:
                self.add_check("Admin Interface", False, f"Admin interface returned {response.status_code}")
                
        except Exception as e:
            self.add_check("API Endpoints", False, f"API check failed: {str(e)}")
    
    def run_all_checks(self):
        """Run all health checks"""
        print("🏥 Running health checks...")
        
        self.check_database()
        self.check_redis()
        self.check_static_files()
        self.check_media_files()
        self.check_disk_space()
        self.check_memory()
        self.check_api_endpoints()
        
        return self.overall_status
    
    def print_results(self):
        """Print health check results"""
        print("\n📊 Health Check Results:")
        print("=" * 50)
        
        for check in self.checks:
            status_icon = "✅" if check['status'] else "❌"
            print(f"{status_icon} {check['name']}: {check['message']}")
        
        print("=" * 50)
        overall_status = "✅ HEALTHY" if self.overall_status else "❌ UNHEALTHY"
        print(f"Overall Status: {overall_status}")
        
        return self.overall_status

def main():
    checker = HealthChecker()
    checker.run_all_checks()
    is_healthy = checker.print_results()
    
    # Exit with appropriate code
    sys.exit(0 if is_healthy else 1)

if __name__ == '__main__':
    main()
