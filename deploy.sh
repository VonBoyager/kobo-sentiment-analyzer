#!/bin/bash
set -e

echo "Installing Docker..."
curl -fsSL https://get.docker.com -o get-docker.sh && sh get-docker.sh

echo "Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

echo "Installing Node.js..."
curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && apt install -y nodejs

echo "Configuring firewall..."
ufw allow ssh && ufw allow 80 && ufw allow 443 && ufw --force enable

echo "Cloning repository..."
cd ~ && git clone https://github.com/VonBoyager/kobo-sentiment-analyzer.git && cd kobo-sentiment-analyzer

echo "Setting up environment..."
cp env.digitalocean .env
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_urlsafe(50))" >> .env
sed -i 's|ALLOWED_HOSTS=.*|ALLOWED_HOSTS=152.42.220.146,localhost,127.0.0.1|' .env
sed -i '/SECRET_KEY=PASTE_YOUR_KEY_HERE/d' .env
sed -i '/SECRET_KEY=your-production-secret-key-here/d' .env

echo "Building frontend..."
cd frontend && npm install && npm run build && cd ..

echo "Starting Docker services..."
docker-compose build && docker-compose up -d

echo "Waiting for services..."
sleep 15

echo "Running migrations..."
docker-compose exec web python manage.py migrate --settings=sentiment_analyzer.settings_production

echo "Collecting static files..."
docker-compose exec web python manage.py collectstatic --noinput --settings=sentiment_analyzer.settings_production

echo "Deployment complete! Check status:"
docker-compose ps

