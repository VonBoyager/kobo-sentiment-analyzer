#!/usr/bin/env python3
"""
Deployment script for Kobo Sentiment Analyzer
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

class DeploymentManager:
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
            sys.exit(1)
        return result.stdout
    
    def check_requirements(self):
        """Check if all requirements are met"""
        print("🔍 Checking requirements...")
        
        # Check Python version
        if sys.version_info < (3, 8):
            print("❌ Python 3.8+ is required")
            sys.exit(1)
        
        # Check if .env file exists
        env_file = self.project_root / '.env'
        if not env_file.exists():
            print("❌ .env file not found. Please create one from env.example")
            sys.exit(1)
        
        # Check if Docker is installed
        try:
            self.run_command("docker --version")
            self.run_command("docker-compose --version")
        except:
            print("❌ Docker and Docker Compose are required for containerized deployment")
            sys.exit(1)
        
        print("✅ All requirements met")
    
    def build_frontend(self):
        """Build frontend assets"""
        print("🏗️ Building frontend...")
        
        frontend_dir = self.project_root / 'frontend'
        if not frontend_dir.exists():
            print("❌ Frontend directory not found")
            sys.exit(1)
        
        # Install dependencies
        self.run_command("npm install", cwd=frontend_dir)
        
        # Build frontend
        self.run_command("npm run build", cwd=frontend_dir)
        
        print("✅ Frontend built successfully")
    
    def run_migrations(self):
        """Run database migrations"""
        print("🗄️ Running database migrations...")
        
        self.run_command(
            "python manage.py migrate --settings=sentiment_analyzer.settings_production",
            cwd=self.django_dir
        )
        
        print("✅ Migrations completed")
    
    def collect_static(self):
        """Collect static files"""
        print("📁 Collecting static files...")
        
        self.run_command(
            "python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production",
            cwd=self.django_dir
        )
        
        print("✅ Static files collected")
    
    def create_superuser(self):
        """Create superuser if it doesn't exist"""
        print("👤 Creating superuser...")
        
        try:
            self.run_command(
                "python manage.py createsuperuser --noinput --settings=sentiment_analyzer.settings_production",
                cwd=self.django_dir
            )
        except:
            print("ℹ️ Superuser may already exist or creation was skipped")
    
    def build_docker(self):
        """Build Docker images"""
        print("🐳 Building Docker images...")
        
        self.run_command("docker-compose build")
        
        print("✅ Docker images built")
    
    def start_services(self):
        """Start all services"""
        print("🚀 Starting services...")
        
        self.run_command("docker-compose up -d")
        
        print("✅ Services started")
    
    def stop_services(self):
        """Stop all services"""
        print("🛑 Stopping services...")
        
        self.run_command("docker-compose down")
        
        print("✅ Services stopped")
    
    def restart_services(self):
        """Restart all services"""
        print("🔄 Restarting services...")
        
        self.run_command("docker-compose restart")
        
        print("✅ Services restarted")
    
    def show_logs(self):
        """Show service logs"""
        print("📋 Showing logs...")
        
        self.run_command("docker-compose logs -f")
    
    def backup_database(self):
        """Backup database"""
        print("💾 Backing up database...")
        
        backup_dir = self.project_root / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        self.run_command(
            f"docker-compose exec -T db pg_dump -U postgres sentiment_analyzer > {backup_dir}/backup_$(date +%Y%m%d_%H%M%S).sql"
        )
        
        print("✅ Database backed up")
    
    def restore_database(self, backup_file):
        """Restore database from backup"""
        print(f"🔄 Restoring database from {backup_file}...")
        
        if not Path(backup_file).exists():
            print(f"❌ Backup file {backup_file} not found")
            sys.exit(1)
        
        self.run_command(f"docker-compose exec -T db psql -U postgres sentiment_analyzer < {backup_file}")
        
        print("✅ Database restored")
    
    def health_check(self):
        """Check service health"""
        print("🏥 Checking service health...")
        
        try:
            import requests
            response = requests.get("http://localhost:8000/api/health/", timeout=10)
            if response.status_code == 200:
                print("✅ Application is healthy")
            else:
                print(f"❌ Application health check failed: {response.status_code}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
    
    def deploy(self):
        """Full deployment process"""
        print("🚀 Starting deployment...")
        
        self.check_requirements()
        self.build_frontend()
        self.build_docker()
        self.start_services()
        
        # Wait for services to be ready
        print("⏳ Waiting for services to be ready...")
        import time
        time.sleep(30)
        
        self.run_migrations()
        self.collect_static()
        self.create_superuser()
        self.health_check()
        
        print("🎉 Deployment completed successfully!")
        print("🌐 Application is available at: http://localhost:8000")
        print("📊 Admin panel: http://localhost:8000/admin/")
        print("🔧 API documentation: http://localhost:8000/api/")

def main():
    parser = argparse.ArgumentParser(description='Kobo Sentiment Analyzer Deployment Manager')
    parser.add_argument('command', choices=[
        'deploy', 'build', 'start', 'stop', 'restart', 'logs', 
        'migrate', 'collectstatic', 'backup', 'restore', 'health'
    ], help='Deployment command to run')
    parser.add_argument('--backup-file', help='Backup file for restore command')
    
    args = parser.parse_args()
    
    manager = DeploymentManager()
    
    if args.command == 'deploy':
        manager.deploy()
    elif args.command == 'build':
        manager.build_frontend()
        manager.build_docker()
    elif args.command == 'start':
        manager.start_services()
    elif args.command == 'stop':
        manager.stop_services()
    elif args.command == 'restart':
        manager.restart_services()
    elif args.command == 'logs':
        manager.show_logs()
    elif args.command == 'migrate':
        manager.run_migrations()
    elif args.command == 'collectstatic':
        manager.collect_static()
    elif args.command == 'backup':
        manager.backup_database()
    elif args.command == 'restore':
        if not args.backup_file:
            print("❌ --backup-file is required for restore command")
            sys.exit(1)
        manager.restore_database(args.backup_file)
    elif args.command == 'health':
        manager.health_check()

if __name__ == '__main__':
    main()
