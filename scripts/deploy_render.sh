#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment variables
source .env

# Check if RENDER_API_KEY is set
if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${RED}Error: RENDER_API_KEY not set in .env file${NC}"
    exit 1
fi

echo "🚀 Deploying Healthcare Simulation API to Render..."

# Deploy to Render using API
RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer ${RENDER_API_KEY}" \
    -H "Content-Type: application/json" \
    -d @render_config.json \
    "https://api.render.com/v1/services")

# Extract service ID from response
SERVICE_ID=$(echo $RESPONSE | jq -r '.id')

if [ -z "$SERVICE_ID" ] || [ "$SERVICE_ID" == "null" ]; then
    echo -e "${RED}❌ Failed to deploy service${NC}"
    echo $RESPONSE
    exit 1
fi

echo -e "${GREEN}✅ Service deployed successfully!${NC}"
echo "Service ID: $SERVICE_ID"

# Wait for deployment to complete
echo "Waiting for deployment to complete..."
for i in {1..30}; do
    STATUS=$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \
        "https://api.render.com/v1/services/${SERVICE_ID}" | jq -r '.status')
    
    if [ "$STATUS" == "live" ]; then
        echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
        break
    fi
    
    echo "Current status: $STATUS"
    sleep 10
done

# Get the service URL
SERVICE_URL=$(curl -s -H "Authorization: Bearer ${RENDER_API_KEY}" \
    "https://api.render.com/v1/services/${SERVICE_ID}" | jq -r '.url')

echo -e "\n${GREEN}🎉 Deployment Complete!${NC}"
echo "Service URL: $SERVICE_URL"
echo "Health Check: $SERVICE_URL/health"
echo "API Documentation: $SERVICE_URL/docs" 