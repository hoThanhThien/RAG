# Dockerfile cho Frontend (Vite)
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build arguments for Vite SPA
ARG VITE_API_URL=http://localhost:8000
ARG VITE_WS_URL=ws://localhost:8000
ARG VITE_PAYPAL_CLIENT_ID=AY8EQiP4YtZbUTQ7uWw85ACV2FMEjwfi1YQGs9gDOXC0Q62rfjXuj2VM44Ku0RqJbAM0_W2qkip_F3pw
ARG VITE_BANK_CODE=970422
ARG VITE_BANK_NAME="MB Bank"
ARG VITE_BANK_ACCOUNT=0375227764
ARG VITE_BANK_HOLDER="HO THANH THIEN"
ARG VITE_APP_NAME=NHom09

ENV VITE_API_URL=$VITE_API_URL
ENV VITE_WS_URL=$VITE_WS_URL
ENV VITE_PAYPAL_CLIENT_ID=$VITE_PAYPAL_CLIENT_ID
ENV VITE_BANK_CODE=$VITE_BANK_CODE
ENV VITE_BANK_NAME=$VITE_BANK_NAME
ENV VITE_BANK_ACCOUNT=$VITE_BANK_ACCOUNT
ENV VITE_BANK_HOLDER=$VITE_BANK_HOLDER
ENV VITE_APP_NAME=$VITE_APP_NAME

# Build the application
RUN npm run build

# Production stage
FROM node:20-alpine

WORKDIR /app

# Install serve to serve the static files
RUN npm install -g serve

# Copy built files from builder
COPY --from=builder /app/dist ./dist

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:3000/ || exit 1

# Run application
CMD ["serve", "-s", "dist", "-l", "3000"]
