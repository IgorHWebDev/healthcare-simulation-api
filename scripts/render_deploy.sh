#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Load environment variables from .env
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading environment variables from .env file...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Check if RENDER_API_KEY is set
if [ -z "$RENDER_API_KEY" ]; then
    echo -e "${RED}Error: RENDER_API_KEY environment variable is not set in .env file${NC}"
    exit 1
fi

echo -e "${YELLOW}Starting Render deployment...${NC}"

# Use the known service ID
SERVICE_ID="srv-cu9lfijqf0us73c1ftfg"
echo -e "${GREEN}Using service ID: $SERVICE_ID${NC}"

# Trigger deployment
echo -e "${YELLOW}Triggering deployment...${NC}"
render deploys create $SERVICE_ID --output json --confirm

# Monitor deployment
echo -e "${YELLOW}Monitoring deployment logs...${NC}"
render logs -r $SERVICE_ID --tail --confirm

echo -e "\n${GREEN}Deployment process completed!${NC}"
echo -e "View your service at: https://healthcare-simulation-api.onrender.com"
echo -e "Monitor logs with: render logs -r $SERVICE_ID --tail --confirm"
