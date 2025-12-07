# Application Size After Installation

## Total Installed Size: **~4,165 MB (4.07 GB)**

This is the current size of the repository with all dependencies installed.

## Detailed Breakdown

### 1. Application Source Code
- **Python source files**: 0.38 MB (70 files)
- **Frontend source files**: 0.13 MB (18 files)
- **Design frontend source**: 0.29 MB (65 files)
- **Configuration files**: ~2.37 MB (docs, configs, etc.)
- **Total Application Code**: ~3.17 MB

### 2. Node.js Dependencies (Installed)

#### Main Frontend (`kobo-sentiment-analyzer-master/frontend/node_modules`)
- **Size**: 178.67 MB
- **Files**: 10,918 files
- **Packages**: React, Vite, TypeScript, TailwindCSS, Axios, Recharts, etc.

#### Design Frontend (`Design/node_modules`)
- **Size**: 164.13 MB
- **Files**: 13,586 files
- **Packages**: React, Radix UI components, Vite, TypeScript, etc.

**Total Node.js Dependencies**: **342.80 MB**

### 3. Python Dependencies (Estimated - Not Currently Installed)

Based on `requirements.txt`, when installed in a virtual environment:

**Core Django Stack**: ~50-60 MB
- Django 5.2.5
- djangorestframework
- django-cors-headers
- gunicorn
- whitenoise

**Machine Learning Libraries**: ~80-100 MB
- scikit-learn 1.4.0 (~50-60 MB)
- pandas 2.2.0 (~20-30 MB)
- numpy 1.26.3 (~15-20 MB)
- joblib 1.3.2
- nltk 3.8.1 (~10-15 MB with data)

**Data Processing**: ~30-40 MB
- matplotlib 3.8.3
- seaborn 0.13.1
- plotly 5.17.0
- openpyxl 3.1.2
- xlrd 2.0.1

**Database & Caching**: ~10-15 MB
- psycopg2-binary 2.9.9
- django-redis 5.4.0
- redis client libraries

**Background Tasks**: ~5-10 MB
- celery 5.3.4

**Other Dependencies**: ~20-30 MB
- requests, urllib3
- cryptography
- python-decouple
- pytest and testing tools
- black, flake8, isort
- boto3, django-storages
- sentry-sdk

**Estimated Total Python Packages**: **~195-255 MB**

*Note: This is an estimate. Actual size depends on:*
- *Python version*
- *Operating system*
- *Whether packages are compiled or binary*
- *Shared dependencies between packages*

### 4. Build Artifacts

#### Frontend Build (`frontend/dist`)
- **Size**: 0.67 MB
- **Files**: 3 files (compiled JS and CSS)

#### Django Static Files (`sentiment_analyzer/staticfiles`)
- **Size**: 3.34 MB
- **Files**: 165 files
- **Includes**: Django admin static files, REST framework assets, frontend static files

**Total Build Artifacts**: **~4.01 MB**

### 5. Data Files

#### Media & ML Models (`sentiment_analyzer/media`)
- **Size**: 3,976.03 MB (~3.9 GB)
- **Files**: 115 files
- **Content**: Trained ML models, uploaded media files
- **Note**: This is the largest component and should be managed separately in production

#### CSV Datasets
- **Size**: ~1.25 MB
- **Files**: 3 files (employee feedback datasets)

**Total Data Files**: **~3,977 MB**

## Complete Installation Size Summary

| Component | Size (MB) | Percentage |
|-----------|-----------|------------|
| **Media/ML Models** | 3,976.03 | 95.5% |
| **Node.js Dependencies** | 342.80 | 8.2% |
| **Python Dependencies** (estimated) | 195-255 | 4.7-6.1% |
| **Application Source Code** | 3.17 | 0.08% |
| **Build Artifacts** | 4.01 | 0.10% |
| **Data Files (CSV)** | 1.25 | 0.03% |
| **TOTAL** | **~4,523-4,583 MB** | **100%** |

## Size Without Media/ML Models

If we exclude the media/ML models directory (which should be stored separately):

| Component | Size (MB) |
|-----------|-----------|
| Node.js Dependencies | 342.80 |
| Python Dependencies (estimated) | 195-255 |
| Application Source Code | 3.17 |
| Build Artifacts | 4.01 |
| Data Files | 1.25 |
| **TOTAL (without media)** | **~546-606 MB** |

## Production Deployment Size

### Docker Image (Multi-stage Build)
- **Base Python image**: ~150-200 MB
- **Application code**: ~3.17 MB
- **Python packages**: ~195-255 MB
- **Frontend build**: ~0.67 MB
- **Static files**: ~3.34 MB
- **Total Docker image**: **~350-460 MB** (compressed)

### Runtime Containers
- **Django app container**: ~350-460 MB
- **PostgreSQL**: ~200 MB
- **Redis**: ~50 MB
- **Nginx**: ~25 MB
- **Total containers**: **~625-735 MB** (excluding data volumes)

### Data Volumes (Separate)
- **Media/ML models**: 3,976 MB (should be on external storage)
- **Database data**: Variable (PostgreSQL data)
- **Static files**: 3.34 MB (can be on CDN)

## Recommendations

1. **Media/ML Models (3.9 GB)**: 
   - Store on external storage (S3, Cloudflare R2, Azure Blob)
   - Use model versioning and cleanup old models
   - Compress model files where possible

2. **Node Modules (343 MB)**:
   - Already excluded from Docker builds using multi-stage builds
   - Only build artifacts are included in final image

3. **Python Packages (195-255 MB)**:
   - Consider using Alpine Linux base image to reduce size
   - Remove development dependencies in production
   - Use pip cache for faster builds

4. **Static Files (3.34 MB)**:
   - Serve from CDN in production
   - Can be excluded from Docker image if using CDN

## Size Comparison

- **Source code only**: ~3.17 MB (0.08% of total)
- **With dependencies (no media)**: ~546-606 MB
- **Full installation (with media)**: ~4,523-4,583 MB
- **Production Docker image**: ~350-460 MB

The application code itself is very small (~3 MB). The majority of the size comes from:
1. Media/ML models (3.9 GB) - should be external
2. Node.js dependencies (343 MB) - excluded from Docker
3. Python dependencies (195-255 MB) - included in Docker

