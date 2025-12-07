#!/usr/bin/env python3
"""
Environment setup script for Kobo Sentiment Analyzer
This script helps you set up the environment configuration
"""

import os
import shutil
from pathlib import Path

def setup_environment():
    """Set up the environment configuration"""
    print("🚀 Setting up Kobo Sentiment Analyzer Environment...")
    
    # Check if environment file exists
    env_file = Path('.env')
    env_example = Path('env.example')
    env_local = Path('environment.env')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return
    
    # Copy from example or create new
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from env.example")
    elif env_local.exists():
        shutil.copy(env_local, env_file)
        print("✅ Created .env file from environment.env")
    else:
        create_env_file()
        print("✅ Created new .env file")
    
    print("\n📝 Environment setup complete!")
    print("You can now edit the .env file to customize your settings.")
    print("\nNext steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Run: pip install -r requirements.txt")
    print("3. Run: python sentiment_analyzer/manage.py migrate")
    print("4. Run: python sentiment_analyzer/manage.py runserver")

def create_env_file():
    """Create a new .env file with default values"""
    env_content = """# Django Settings
SECRET_KEY=django-insecure-*hc=ugfil%bz9h90aeoql=d68cu(i5tv9u1=@5&8i5)tcbn9yk
DEBUG=True
ALLOWED_HOSTS=152.42.220.146,localhost,127.0.0.1

# Database Configuration
DB_ENGINE=django.db.backends.postgresql
DB_NAME=sentiment_analyzer
DB_USER=postgres
DB_PASSWORD=hellow1432
DB_HOST=db
DB_PORT=5432

# Redis Configuration (for caching and sessions)
REDIS_URL=redis://redis:6379/0

# Email Configuration
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# AWS Configuration (for production)
AWS_ACCESS_KEY_ID=your-aws-access-key
AWS_SECRET_ACCESS_KEY=your-aws-secret-key
AWS_STORAGE_BUCKET_NAME=your-s3-bucket
AWS_S3_REGION_NAME=us-east-1

# API Configuration
API_RATE_LIMIT=1000
API_RATE_LIMIT_WINDOW=3600

# ML Model Configuration
ML_MODEL_CACHE_SIZE=10
ML_MODEL_UPDATE_INTERVAL=86400

# Logging Configuration
LOG_LEVEL=INFO
LOG_FILE=logs/django.log

# Frontend Configuration
FRONTEND_BUILD_DIR=frontend/dist
VITE_DEV_SERVER_URL=http://localhost:3000
"""
    
    with open('.env', 'w') as f:
        f.write(env_content)

if __name__ == '__main__':
    setup_environment()
