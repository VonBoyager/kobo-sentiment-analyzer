# Deployment Notes

## Frontend Port Configuration

This project contains two frontend applications:

1. **Main Frontend** (`kobo-sentiment-analyzer-master/frontend/`):
   - Development port: 5173
   - Build output: `dist/`
   - Integrated with Django backend
   - **This is the frontend used in production deployment**

2. **Design Frontend** (`Design/`):
   - Development port: 3000
   - Build output: `build/`
   - Separate React application
   - **Note**: This appears to be a separate design/prototype application and is NOT integrated with the main deployment

### Deployment Recommendation

- **For production**: Use only the main frontend (`kobo-sentiment-analyzer-master/frontend/`)
- **For development**: The Design frontend can run independently on port 3000, but ensure the main frontend uses port 5173 to avoid conflicts

## Static Files Configuration

Static files are configured as follows:
- Django collects static files to `/app/static` in the web container
- This directory is mounted to `/var/www/static` in both web and nginx containers
- Nginx serves static files from `/var/www/static/`
- Media files follow the same pattern with `/app/media` and `/var/www/media`

## Environment Files

- `env.example`: Template for local development
- `env.production`: Template for production deployment (DO NOT commit actual secrets)
- `env.digitalocean`: Template for Digital Ocean deployment (DO NOT commit actual secrets)

**Important**: Always set `SECRET_KEY` and `DB_PASSWORD` in your actual `.env` file. Never commit these values to version control.

## Gunicorn Workers

All deployments use 3 Gunicorn workers for consistency:
- `Dockerfile`: 3 workers
- `docker-compose.yml`: 3 workers

