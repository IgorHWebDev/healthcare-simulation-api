#!/bin/bash

# IQHIS Public Deployment Script
# Version: 0.1.0-sprint.0
# Environment: Production

set -e

# Load environment variables
source .env

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "Starting IQHIS public deployment..."

# 1. SSL Certificate Setup
echo -e "${GREEN}Setting up SSL certificates...${NC}"
certbot certonly --nginx \
    -d api.iqhis.com \
    -d staging.api.iqhis.com \
    --agree-tos \
    --email ${ADMIN_EMAIL} \
    --non-interactive

# 2. Nginx Configuration
echo -e "${GREEN}Configuring Nginx...${NC}"
sudo cp config/nginx/iqhis.conf /etc/nginx/conf.d/
sudo nginx -t
sudo systemctl reload nginx

# 3. Security Setup
echo -e "${GREEN}Setting up security configurations...${NC}"
# Generate JWT public key
openssl rsa -in ${JWT_PRIVATE_KEY} -pubout -out /etc/nginx/jwt_pub.key

# 4. Monitoring Setup
echo -e "${GREEN}Setting up monitoring...${NC}"
# Install Prometheus
sudo cp config/monitoring/prometheus.yml /etc/prometheus/
sudo systemctl restart prometheus

# Install Node Exporter
sudo systemctl start node_exporter

# Install Nginx Exporter
sudo systemctl start nginx-prometheus-exporter

# 5. Rate Limiting Setup
echo -e "${GREEN}Configuring rate limiting...${NC}"
sudo cp config/nginx/rate_limit.conf /etc/nginx/conf.d/

# 6. Firewall Configuration
echo -e "${GREEN}Configuring firewall...${NC}"
sudo ufw allow 443/tcp
sudo ufw allow 80/tcp
sudo ufw reload

# 7. Health Check
echo -e "${GREEN}Performing health check...${NC}"
curl -k https://localhost/v1/quantum/health

# 8. Monitoring Check
echo -e "${GREEN}Verifying monitoring...${NC}"
curl -s http://localhost:9090/-/healthy

echo -e "${GREEN}Deployment completed successfully!${NC}"

# Print verification steps
echo -e "\nVerification Steps:"
echo "1. Check SSL: https://api.iqhis.com/v1/quantum/health"
echo "2. Check Metrics: https://api.iqhis.com/v1/metrics (requires auth)"
echo "3. Check Prometheus: http://localhost:9090/targets"
echo "4. Check Nginx status: systemctl status nginx" 