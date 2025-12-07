# Application Size Analysis

## Summary

**Total Application Size: ~4,165 MB (4.07 GB)**

This includes all files in the repository including dependencies, build artifacts, and data files.

## Breakdown by Component

### 1. Application Source Code
- **Python Code**: 0.38 MB (70 files)
- **Frontend Source Code**: 0.13 MB (18 files)
- **Total Source Code**: ~0.51 MB

### 2. Dependencies

#### Python Packages (estimated)
- **Size**: ~150-200 MB (when installed in virtual environment)
- **Packages**: 40+ packages including:
  - Django 5.2.5
  - scikit-learn, pandas, numpy (ML libraries)
  - djangorestframework
  - celery, redis
  - gunicorn
  - And many more (see requirements.txt)

#### Node.js Packages
- **Main Frontend (kobo-sentiment-analyzer-master/frontend)**:
  - node_modules: 178.67 MB (10,918 files)
  - Dependencies: React, Vite, TypeScript, TailwindCSS, etc.
  
- **Design Frontend (Design/)**:
  - node_modules: Not installed (or not found)
  - Would be similar size (~150-200 MB) if installed

### 3. Build Artifacts

#### Frontend Build
- **Main Frontend dist/**: 0.67 MB (3 files)
  - Compiled JavaScript and CSS bundles

#### Static Files
- **Django staticfiles/**: 3.34 MB (165 files)
  - Admin static files
  - REST framework static files
  - Frontend static assets

### 4. Data Files

#### Media Files
- **ML Models & Media**: 3,976.03 MB (~3.9 GB, 115 files)
  - Machine learning model files
  - Uploaded media files
  - This is the largest component

#### Database Files
- **SQLite database**: Included in sentiment_analyzer directory
- **CSV datasets**: employee_feedback_dataset.csv, etc.

### 5. Directory Sizes (Top Contributors)

1. **sentiment_analyzer/**: 3,980.7 MB
   - Includes media files (ML models)
   - Static files
   - Python source code
   - Database files

2. **frontend/**: 179.61 MB
   - node_modules: 178.67 MB
   - Source code: 0.13 MB
   - Build artifacts: 0.67 MB

3. **static/**: 3.4 MB
   - Static file copies

4. **Other directories**: < 1 MB combined

## Size Without Dependencies

If we exclude:
- node_modules (~179 MB)
- Python packages (~150-200 MB when installed)
- Media/ML models (~3.9 GB)
- Build artifacts (~4 MB)

**Pure Application Code**: ~0.51 MB

## Production Deployment Size

### Docker Image (estimated)
- Base Python image: ~150-200 MB
- Application code: ~0.51 MB
- Python packages: ~150-200 MB
- Frontend build: ~0.67 MB
- Static files: ~3.34 MB
- **Total Docker image**: ~300-400 MB (compressed)

### Runtime Requirements
- PostgreSQL: Separate container (~200 MB)
- Redis: Separate container (~50 MB)
- Nginx: Separate container (~25 MB)

**Total containerized deployment**: ~575-675 MB (excluding data volumes)

## Recommendations

1. **Media/ML Models**: 3.9 GB is very large - consider:
   - Using external storage (S3, Cloudflare R2)
   - Model versioning and cleanup
   - Compressing model files

2. **Node Modules**: Can be excluded from Docker builds using multi-stage builds (already implemented)

3. **Static Files**: Already optimized, can be served from CDN

4. **Database**: SQLite is included but production uses PostgreSQL (separate container)

## Notes

- The Design/ frontend is a separate application and not included in the main deployment
- Media files and ML models are the largest component and should be managed separately
- Python packages are installed at runtime, not stored in the repository
- Build artifacts are generated during deployment, not stored in source control

