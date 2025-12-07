# Commands to Update Droplet After Package.json Fix

Run these commands in your Digital Ocean droplet console to update to the fixed version:

## Step 1: Pull Latest Changes
```bash
cd kobo-sentiment-analyzer
git pull origin main
```

## Step 2: Clean Install Dependencies
```bash
# Remove old node_modules and lock file
cd frontend
rm -rf node_modules package-lock.json

# Install with updated packages
npm install

# Build frontend
npm run build
cd ..
```

## Step 3: Rebuild Docker Containers
```bash
# Stop containers
docker-compose down

# Rebuild (this will use the new package.json)
docker-compose build --no-cache frontend

# Or rebuild all
docker-compose build --no-cache

# Start services
docker-compose up -d
```

## Step 4: Verify
```bash
# Check container status
docker-compose ps

# Check logs for any errors
docker-compose logs frontend
docker-compose logs web
```

## Alternative: If You Want to Upgrade Node Instead

If you prefer to upgrade Node to v20 (recommended for future-proofing):

```bash
# Install Node Version Manager (nvm)
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc

# Install Node 20
nvm install 20
nvm use 20
nvm alias default 20

# Verify
node --version  # Should show v20.x.x

# Then rebuild
cd kobo-sentiment-analyzer/frontend
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..
docker-compose build --no-cache
docker-compose up -d
```

## What Was Fixed

1. **react-router-dom**: Downgraded from v7.10.1 to v6.26.0 (compatible with Node 18)
2. **ESLint**: Updated to v9.0.0 (removes deprecated warnings)
3. **Type definitions**: Updated to match Node 18
4. **Vite**: Downgraded to v5.4.0 (more stable with Node 18)

The code is fully compatible with React Router v6 - no code changes needed!

