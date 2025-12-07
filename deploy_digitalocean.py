#!/usr/bin/env python3
"""
Digital Ocean deployment script for Kobo Sentiment Analyzer
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class DigitalOceanDeployment:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.django_dir = self.project_root / 'sentiment_analyzer'
        
    def run_command(self, command, cwd=None):
        """Run a shell command"""
        if cwd is None:
            cwd = self.project_root
        print(f"Running: {command}")
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"Error: {result.stderr}")
            return False
        print(result.stdout)
        return True
    
    def check_requirements(self):
        """Check if all requirements are met"""
        print("🔍 Checking Digital Ocean deployment requirements...")
        
        # Check if Docker is installed
        if not self.run_command("docker --version"):
            print("❌ Docker not found. Install Docker first.")
            return False
        
        # Check if Docker Compose is installed
        if not self.run_command("docker-compose --version"):
            print("❌ Docker Compose not found. Install Docker Compose first.")
            return False
        
        # Check if .env file exists
        env_file = self.project_root / '.env'
        if not env_file.exists():
            print("❌ .env file not found. Copy env.digitalocean to .env and configure it.")
            return False
        
        print("✅ All requirements met")
        return True
    
    def setup_firewall(self):
        """Setup UFW firewall for Digital Ocean"""
        print("🔥 Setting up firewall...")
        
        commands = [
            "sudo ufw allow ssh",
            "sudo ufw allow 80",
            "sudo ufw allow 443",
            "sudo ufw --force enable"
        ]
        
        for cmd in commands:
            if not self.run_command(cmd):
                print(f"⚠️ Warning: Failed to run {cmd}")
        
        print("✅ Firewall configured")
    
    def setup_ssl(self, domain=None):
        """Setup SSL with Let's Encrypt"""
        if not domain:
            print("⚠️ No domain provided, skipping SSL setup")
            return True
        
        print(f"🔒 Setting up SSL for {domain}...")
        
        # Install certbot
        commands = [
            "sudo apt update",
            "sudo apt install -y certbot python3-certbot-nginx",
            f"sudo certbot --nginx -d {domain} -d www.{domain} --non-interactive --agree-tos --email admin@{domain}"
        ]
        
        for cmd in commands:
            if not self.run_command(cmd):
                print(f"⚠️ Warning: Failed to run {cmd}")
        
        print("✅ SSL configured")
    
    def build_and_deploy(self):
        """Build and deploy the application"""
        print("🚀 Building and deploying application...")
        
        # Build frontend
        if not self.run_command("npm install", cwd=self.project_root / 'frontend'):
            print("❌ Frontend build failed")
            return False
        
        if not self.run_command("npm run build", cwd=self.project_root / 'frontend'):
            print("❌ Frontend build failed")
            return False
        
        # Build Docker images
        if not self.run_command("docker-compose build"):
            print("❌ Docker build failed")
            return False
        
        # Start services
        if not self.run_command("docker-compose up -d"):
            print("❌ Failed to start services")
            return False
        
        print("✅ Application deployed successfully")
        return True
    
    def run_migrations(self):
        """Run database migrations"""
        print("🗄️ Running database migrations...")
        
        if not self.run_command("docker-compose exec web python manage.py migrate --settings=sentiment_analyzer.settings_production"):
            print("❌ Migrations failed")
            return False
        
        print("✅ Migrations completed")
        return True
    
    def collect_static(self):
        """Collect static files"""
        print("📁 Collecting static files...")
        
        if not self.run_command("docker-compose exec web python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production"):
            print("❌ Static files collection failed")
            return False
        
        print("✅ Static files collected")
        return True
    
    def create_superuser(self):
        """Create superuser"""
        print("👤 Creating superuser...")
        
        if not self.run_command("docker-compose exec web python manage.py createsuperuser --settings=sentiment_analyzer.settings_production"):
            print("ℹ️ Superuser creation skipped (may already exist)")
        
        print("✅ Superuser setup completed")
        return True
    
    def health_check(self):
        """Check application health"""
        print("🏥 Checking application health...")
        
        try:
            import requests
            response = requests.get("http://localhost/api/health/", timeout=10)
            if response.status_code == 200:
                print("✅ Application is healthy")
                return True
            else:
                print(f"❌ Application health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    def deploy(self, domain=None):
        """Full deployment process"""
        print("🌊 Starting Digital Ocean deployment...")
        
        if not self.check_requirements():
            return False
        
        self.setup_firewall()
        
        if not self.build_and_deploy():
            return False
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        import time
        time.sleep(30)
        
        if not self.run_migrations():
            return False
        
        if not self.collect_static():
            return False
        
        if not self.create_superuser():
            return False
        
        if self.health_check():
            print("🎉 Digital Ocean deployment completed successfully!")
            print("🌐 Application is available at: http://your-droplet-ip")
            if domain:
                print(f"🌐 Domain: https://{domain}")
            print("📊 Admin panel: http://your-droplet-ip/admin/")
            print("🔧 API: http://your-droplet-ip/api/")
            
            if domain:
                self.setup_ssl(domain)
        else:
            print("❌ Deployment completed with issues. Check logs for details.")
            return False
        
        return True

def main():
    parser = argparse.ArgumentParser(description='Digital Ocean Deployment Manager for Kobo Sentiment Analyzer')
    parser.add_argument('command', choices=['deploy', 'build', 'start', 'stop', 'restart', 'logs', 'health'], 
                       help='Deployment command to run')
    parser.add_argument('--domain', help='Domain name for SSL setup')
    
    args = parser.parse_args()
    
    deployment = DigitalOceanDeployment()
    
    if args.command == 'deploy':
        deployment.deploy(args.domain)
    elif args.command == 'build':
        deployment.build_and_deploy()
    elif args.command == 'start':
        deployment.run_command("docker-compose up -d")
    elif args.command == 'stop':
        deployment.run_command("docker-compose down")
    elif args.command == 'restart':
        deployment.run_command("docker-compose restart")
    elif args.command == 'logs':
        deployment.run_command("docker-compose logs -f")
    elif args.command == 'health':
        deployment.health_check()

if __name__ == '__main__':
    main()
