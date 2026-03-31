# Docker Build & Push Script for AWS ECR

## Setup AWS ECR (Elastic Container Registry)

### Step 1: Login to AWS CLI
```bash
aws configure
```

### Step 2: Create ECR Repositories
```bash
# Backend
aws ecr create-repository --repository-name nhom09-backend --region ap-southeast-1

# Frontend  
aws ecr create-repository --repository-name nhom09-frontend --region ap-southeast-1
```

### Step 3: Build and Push Images

#### For Backend:
```bash
# Set variables
AWS_ACCOUNT_ID=your-account-id
AWS_REGION=ap-southeast-1
IMAGE_NAME=nhom09-backend
IMAGE_TAG=latest

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Build image
docker build -t $IMAGE_NAME:$IMAGE_TAG ./backend

# Tag image for ECR
docker tag $IMAGE_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG
docker tag $IMAGE_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:latest

# Push to ECR
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:latest
```

#### For Frontend:
```bash
IMAGE_NAME=nhom09-frontend

# Build image
docker build -t $IMAGE_NAME:$IMAGE_TAG ./frontend

# Tag and push
docker tag $IMAGE_NAME:$IMAGE_TAG $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG
docker push $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$IMAGE_NAME:$IMAGE_TAG
```

## Docker Compose for EC2

Save as `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  backend:
    image: your-account-id.dkr.ecr.ap-southeast-1.amazonaws.com/nhom09-backend:latest
    restart: always
    ports:
      - "8000:8000"
    environment:
      - PAYPAL_MODE=sandbox
      - PAYPAL_CLIENT_ID=${PAYPAL_CLIENT_ID}
      - PAYPAL_CLIENT_SECRET=${PAYPAL_CLIENT_SECRET}
      - DATABASE_URL=${DATABASE_URL}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - /home/ubuntu/uploads:/app/uploads
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    image: your-account-id.dkr.ecr.ap-southeast-1.amazonaws.com/nhom09-frontend:latest
    restart: always
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=https://your-domain.com/api
```

## Local Testing

```bash
# Build locally
docker-compose build

# Run
docker-compose up -d

# Test
curl http://localhost:8000
curl http://localhost:5173
```
