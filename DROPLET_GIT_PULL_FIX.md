# Fix Git Pull Conflict on Droplet

When you see this error:
```
error: Your local changes to the following files would be overwritten by merge:
        frontend/package-lock.json
```

## Solution: Discard Local Changes and Pull

Run these commands on your droplet:

```bash
cd kobo-sentiment-analyzer

# Option 1: Discard local changes to package-lock.json (recommended)
git checkout -- frontend/package-lock.json
git pull origin main

# Option 2: Stash changes, pull, then reinstall
git stash
git pull origin main
git stash pop  # This might cause conflicts, so Option 1 is better

# Option 3: Force reset to remote (if you don't care about local changes)
git fetch origin
git reset --hard origin/main
```

## After Pulling, Reinstall Dependencies

```bash
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..
```

## Complete Update Sequence

```bash
cd kobo-sentiment-analyzer

# Discard local package-lock.json changes
git checkout -- frontend/package-lock.json

# Pull latest changes
git pull origin main

# Clean and reinstall frontend dependencies
cd frontend
rm -rf node_modules package-lock.json
npm install
npm run build
cd ..

# Rebuild Docker containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# Run migrations and collect static files
docker-compose exec web python manage.py migrate --settings=sentiment_analyzer.settings_production
docker-compose exec web python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production
```

