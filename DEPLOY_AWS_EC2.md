# Deploy Guide for AWS EC2

## Prerequisites
- AWS EC2 instance with Ubuntu 22.04 LTS
- Elastic IP allocated
- Security Group with ports: 22 (SSH), 80 (HTTP), 443 (HTTPS), 8000 (API)
- Domain name (optional, for HTTPS)

## Step 1: SSH vào EC2
```bash
ssh -i your-key.pem ubuntu@your-ec2-ip
```

## Step 2: Install Docker & Docker Compose
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/v2.20.0/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installations
docker --version
docker-compose --version
```

## Step 3: Clone Repository
```bash
cd /home/ubuntu
git clone https://github.com/your-username/NHom09.git
cd NHom09
```

## Step 4: Setup Environment Variables
```bash
# Create .env file
nano .env
```

Add the following variables:
```
PAYPAL_MODE=sandbox
PAYPAL_CLIENT_ID=your-paypal-client-id
PAYPAL_CLIENT_SECRET=your-paypal-secret
DATABASE_URL=mysql+pymysql://user:password@db-host:3306/dbname
JWT_SECRET_KEY=your-secret-key-here
```

## Step 5: Build and Run Docker Containers
```bash
# Build images
docker-compose build

# Run in background
docker-compose up -d

# Check logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Step 6: Setup Nginx Reverse Proxy (Optional but Recommended)
```bash
# Install Nginx
sudo apt install -y nginx

# Create config file
sudo nano /etc/nginx/sites-available/default
```

Replace content with:
```nginx
upstream backend {
    server localhost:8000;
}

upstream frontend {
    server localhost:5173;
}

server {
    listen 80 default_server;
    listen [::]:80 default_server;
    
    server_name _;

    # Frontend
    location / {
        proxy_pass http://frontend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # API
    location /api/ {
        proxy_pass http://backend;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Uploads
    location /uploads/ {
        proxy_pass http://backend;
    }
}
```

Enable and restart Nginx:
```bash
sudo systemctl enable nginx
sudo systemctl restart nginx
```

## Step 7: Setup HTTPS with Let's Encrypt (Optional)
```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Get SSL certificate (replace example.com with your domain)
sudo certbot --nginx -d example.com -d www.example.com
```

## Step 8: Manage Services
```bash
# View running containers
docker-compose ps

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Update and redeploy
git pull
docker-compose build
docker-compose up -d
```

## Step 9: Database Setup (if using managed database)
- Create RDS instance on AWS
- Update DATABASE_URL in .env
- Run migrations if needed

## Monitoring & Maintenance

### View real-time logs
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Clean up unused images
```bash
docker system prune -a
```

### Update containers
```bash
git pull
docker-compose build
docker-compose up -d
```

### Backup volumes
```bash
docker run --rm -v nhom09_uploads:/data -v $(pwd):/backup alpine tar czf /backup/uploads-backup.tar.gz -C /data .
```

## Troubleshooting

### Containers won't start
```bash
docker-compose logs backend
docker-compose logs frontend
```

### Port already in use
```bash
sudo lsof -i :8000
sudo lsof -i :5173
sudo kill -9 <PID>
```

### Database connection issues
- Verify DATABASE_URL is correct
- Check security group allows traffic
- Verify database credentials

### Nginx proxy issues
```bash
sudo nginx -t
sudo systemctl restart nginx
```
