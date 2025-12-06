#!/usr/bin/env python3
"""
Backup and recovery manager for Kobo Sentiment Analyzer
"""

import os
import sys
import subprocess
import shutil
import gzip
import json
from datetime import datetime
from pathlib import Path
import psycopg2
from decouple import config

class BackupManager:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.backup_dir = self.project_root / 'backups'
        self.backup_dir.mkdir(exist_ok=True)
        
        # Database configuration
        self.db_config = {
            'host': config('DB_HOST', default='localhost'),
            'port': config('DB_PORT', default='5432'),
            'database': config('DB_NAME', default='sentiment_analyzer'),
            'user': config('DB_USER', default='postgres'),
            'password': config('DB_PASSWORD', default='hellow1432')
        }
    
    def create_backup_name(self, prefix='backup'):
        """Create a timestamped backup name"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}"
    
    def backup_database(self):
        """Backup PostgreSQL database"""
        print("🗄️ Backing up database...")
        
        backup_name = self.create_backup_name('db')
        backup_file = self.backup_dir / f"{backup_name}.sql"
        
        try:
            # Create database dump
            cmd = [
                'pg_dump',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', self.db_config['database'],
                '--no-password',
                '--verbose',
                '--clean',
                '--if-exists',
                '--create'
            ]
            
            with open(backup_file, 'w') as f:
                env = os.environ.copy()
                env['PGPASSWORD'] = self.db_config['password']
                subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, env=env, check=True)
            
            # Compress the backup
            compressed_file = f"{backup_file}.gz"
            with open(backup_file, 'rb') as f_in:
                with gzip.open(compressed_file, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)
            
            # Remove uncompressed file
            backup_file.unlink()
            
            print(f"✅ Database backed up to {compressed_file}")
            return compressed_file
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Database backup failed: {e.stderr.decode()}")
            return None
        except Exception as e:
            print(f"❌ Database backup failed: {str(e)}")
            return None
    
    def backup_media_files(self):
        """Backup media files"""
        print("📁 Backing up media files...")
        
        media_dir = self.project_root / 'sentiment_analyzer' / 'media'
        if not media_dir.exists():
            print("ℹ️ No media directory found")
            return None
        
        backup_name = self.create_backup_name('media')
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            shutil.make_archive(
                str(backup_file.with_suffix('')),
                'gztar',
                media_dir
            )
            
            print(f"✅ Media files backed up to {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Media backup failed: {str(e)}")
            return None
    
    def backup_static_files(self):
        """Backup static files"""
        print("📄 Backing up static files...")
        
        static_dir = self.project_root / 'sentiment_analyzer' / 'static'
        if not static_dir.exists():
            print("ℹ️ No static directory found")
            return None
        
        backup_name = self.create_backup_name('static')
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            shutil.make_archive(
                str(backup_file.with_suffix('')),
                'gztar',
                static_dir
            )
            
            print(f"✅ Static files backed up to {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ Static backup failed: {str(e)}")
            return None
    
    def backup_ml_models(self):
        """Backup ML models"""
        print("🤖 Backing up ML models...")
        
        models_dir = self.project_root / 'sentiment_analyzer' / 'media' / 'ml_models'
        if not models_dir.exists():
            print("ℹ️ No ML models directory found")
            return None
        
        backup_name = self.create_backup_name('models')
        backup_file = self.backup_dir / f"{backup_name}.tar.gz"
        
        try:
            shutil.make_archive(
                str(backup_file.with_suffix('')),
                'gztar',
                models_dir
            )
            
            print(f"✅ ML models backed up to {backup_file}")
            return str(backup_file)
            
        except Exception as e:
            print(f"❌ ML models backup failed: {str(e)}")
            return None
    
    def create_full_backup(self):
        """Create a full backup of everything"""
        print("🔄 Creating full backup...")
        
        backup_name = self.create_backup_name('full')
        backup_info = {
            'timestamp': datetime.now().isoformat(),
            'backup_name': backup_name,
            'files': {}
        }
        
        # Backup database
        db_file = self.backup_database()
        if db_file:
            backup_info['files']['database'] = db_file
        
        # Backup media files
        media_file = self.backup_media_files()
        if media_file:
            backup_info['files']['media'] = media_file
        
        # Backup static files
        static_file = self.backup_static_files()
        if static_file:
            backup_info['files']['static'] = static_file
        
        # Backup ML models
        models_file = self.backup_ml_models()
        if models_file:
            backup_info['files']['models'] = models_file
        
        # Save backup info
        info_file = self.backup_dir / f"{backup_name}_info.json"
        with open(info_file, 'w') as f:
            json.dump(backup_info, f, indent=2)
        
        print(f"✅ Full backup completed: {backup_name}")
        return backup_name
    
    def restore_database(self, backup_file):
        """Restore database from backup"""
        print(f"🔄 Restoring database from {backup_file}...")
        
        if not Path(backup_file).exists():
            print(f"❌ Backup file {backup_file} not found")
            return False
        
        try:
            # Decompress if needed
            if backup_file.endswith('.gz'):
                decompressed_file = backup_file.replace('.gz', '')
                with gzip.open(backup_file, 'rb') as f_in:
                    with open(decompressed_file, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                restore_file = decompressed_file
            else:
                restore_file = backup_file
            
            # Restore database
            cmd = [
                'psql',
                '-h', self.db_config['host'],
                '-p', str(self.db_config['port']),
                '-U', self.db_config['user'],
                '-d', 'postgres'  # Connect to postgres to drop/create database
            ]
            
            with open(restore_file, 'r') as f:
                env = os.environ.copy()
                env['PGPASSWORD'] = self.db_config['password']
                subprocess.run(cmd, stdin=f, env=env, check=True)
            
            # Clean up decompressed file if it was created
            if backup_file.endswith('.gz') and Path(decompressed_file).exists():
                Path(decompressed_file).unlink()
            
            print("✅ Database restored successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Database restore failed: {e.stderr.decode()}")
            return False
        except Exception as e:
            print(f"❌ Database restore failed: {str(e)}")
            return False
    
    def restore_media_files(self, backup_file):
        """Restore media files from backup"""
        print(f"🔄 Restoring media files from {backup_file}...")
        
        if not Path(backup_file).exists():
            print(f"❌ Backup file {backup_file} not found")
            return False
        
        media_dir = self.project_root / 'sentiment_analyzer' / 'media'
        media_dir.mkdir(exist_ok=True)
        
        try:
            shutil.unpack_archive(backup_file, media_dir)
            print("✅ Media files restored successfully")
            return True
        except Exception as e:
            print(f"❌ Media restore failed: {str(e)}")
            return False
    
    def restore_static_files(self, backup_file):
        """Restore static files from backup"""
        print(f"🔄 Restoring static files from {backup_file}...")
        
        if not Path(backup_file).exists():
            print(f"❌ Backup file {backup_file} not found")
            return False
        
        static_dir = self.project_root / 'sentiment_analyzer' / 'static'
        static_dir.mkdir(exist_ok=True)
        
        try:
            shutil.unpack_archive(backup_file, static_dir)
            print("✅ Static files restored successfully")
            return True
        except Exception as e:
            print(f"❌ Static restore failed: {str(e)}")
            return False
    
    def restore_ml_models(self, backup_file):
        """Restore ML models from backup"""
        print(f"🔄 Restoring ML models from {backup_file}...")
        
        if not Path(backup_file).exists():
            print(f"❌ Backup file {backup_file} not found")
            return False
        
        models_dir = self.project_root / 'sentiment_analyzer' / 'media' / 'ml_models'
        models_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            shutil.unpack_archive(backup_file, models_dir)
            print("✅ ML models restored successfully")
            return True
        except Exception as e:
            print(f"❌ ML models restore failed: {str(e)}")
            return False
    
    def restore_full_backup(self, backup_name):
        """Restore from a full backup"""
        print(f"🔄 Restoring full backup: {backup_name}...")
        
        info_file = self.backup_dir / f"{backup_name}_info.json"
        if not info_file.exists():
            print(f"❌ Backup info file {info_file} not found")
            return False
        
        try:
            with open(info_file, 'r') as f:
                backup_info = json.load(f)
            
            success = True
            
            # Restore database
            if 'database' in backup_info['files']:
                if not self.restore_database(backup_info['files']['database']):
                    success = False
            
            # Restore media files
            if 'media' in backup_info['files']:
                if not self.restore_media_files(backup_info['files']['media']):
                    success = False
            
            # Restore static files
            if 'static' in backup_info['files']:
                if not self.restore_static_files(backup_info['files']['static']):
                    success = False
            
            # Restore ML models
            if 'models' in backup_info['files']:
                if not self.restore_ml_models(backup_info['files']['models']):
                    success = False
            
            if success:
                print("✅ Full backup restored successfully")
            else:
                print("⚠️ Backup restore completed with some errors")
            
            return success
            
        except Exception as e:
            print(f"❌ Full backup restore failed: {str(e)}")
            return False
    
    def list_backups(self):
        """List available backups"""
        print("📋 Available backups:")
        
        backup_files = list(self.backup_dir.glob('*_info.json'))
        if not backup_files:
            print("No backups found")
            return
        
        for info_file in sorted(backup_files, reverse=True):
            try:
                with open(info_file, 'r') as f:
                    backup_info = json.load(f)
                
                print(f"\n📦 {backup_info['backup_name']}")
                print(f"   Created: {backup_info['timestamp']}")
                print(f"   Files: {', '.join(backup_info['files'].keys())}")
                
            except Exception as e:
                print(f"❌ Error reading {info_file}: {str(e)}")
    
    def cleanup_old_backups(self, days=30):
        """Clean up backups older than specified days"""
        print(f"🧹 Cleaning up backups older than {days} days...")
        
        cutoff_date = datetime.now().timestamp() - (days * 24 * 60 * 60)
        removed_count = 0
        
        for file_path in self.backup_dir.iterdir():
            if file_path.stat().st_mtime < cutoff_date:
                try:
                    file_path.unlink()
                    removed_count += 1
                    print(f"   Removed: {file_path.name}")
                except Exception as e:
                    print(f"   Error removing {file_path.name}: {str(e)}")
        
        print(f"✅ Cleaned up {removed_count} old backup files")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Kobo Sentiment Analyzer Backup Manager')
    parser.add_argument('command', choices=[
        'backup-db', 'backup-media', 'backup-static', 'backup-models', 
        'backup-full', 'restore-db', 'restore-media', 'restore-static', 
        'restore-models', 'restore-full', 'list', 'cleanup'
    ], help='Backup command to run')
    parser.add_argument('--file', help='Backup file for restore commands')
    parser.add_argument('--backup-name', help='Backup name for restore-full command')
    parser.add_argument('--days', type=int, default=30, help='Days for cleanup command')
    
    args = parser.parse_args()
    
    manager = BackupManager()
    
    if args.command == 'backup-db':
        manager.backup_database()
    elif args.command == 'backup-media':
        manager.backup_media_files()
    elif args.command == 'backup-static':
        manager.backup_static_files()
    elif args.command == 'backup-models':
        manager.backup_ml_models()
    elif args.command == 'backup-full':
        manager.create_full_backup()
    elif args.command == 'restore-db':
        if not args.file:
            print("❌ --file is required for restore-db command")
            sys.exit(1)
        manager.restore_database(args.file)
    elif args.command == 'restore-media':
        if not args.file:
            print("❌ --file is required for restore-media command")
            sys.exit(1)
        manager.restore_media_files(args.file)
    elif args.command == 'restore-static':
        if not args.file:
            print("❌ --file is required for restore-static command")
            sys.exit(1)
        manager.restore_static_files(args.file)
    elif args.command == 'restore-models':
        if not args.file:
            print("❌ --file is required for restore-models command")
            sys.exit(1)
        manager.restore_ml_models(args.file)
    elif args.command == 'restore-full':
        if not args.backup_name:
            print("❌ --backup-name is required for restore-full command")
            sys.exit(1)
        manager.restore_full_backup(args.backup_name)
    elif args.command == 'list':
        manager.list_backups()
    elif args.command == 'cleanup':
        manager.cleanup_old_backups(args.days)

if __name__ == '__main__':
    main()
