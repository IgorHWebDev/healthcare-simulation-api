#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Starting deployment to Render...${NC}"

# Check if required environment variables are set
required_vars=(
    "DB_USER"
    "DB_SECRET"
    "DB_NAME"
    "REDIS_SECRET"
    "JWT_SECRET"
)

missing_vars=()
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo -e "${RED}Error: Missing required environment variables:${NC}"
    printf '%s\n' "${missing_vars[@]}"
    exit 1
fi

# Verify render.yaml exists
if [ ! -f "render.yaml" ]; then
    echo -e "${RED}Error: render.yaml not found${NC}"
    exit 1
fi

# Verify requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}Error: requirements.txt not found${NC}"
    exit 1
fi

# Run pre-deployment checks
echo -e "${YELLOW}Running pre-deployment checks...${NC}"

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Python version: ${python_version}${NC}"

# Check if all required packages are installed
echo -e "${YELLOW}Verifying Python packages...${NC}"
if ! pip install -r requirements.txt --dry-run > /dev/null 2>&1; then
    echo -e "${RED}Error: Some required packages cannot be installed${NC}"
    exit 1
fi
echo -e "${GREEN}All packages verified successfully${NC}"

# Check database schema
echo -e "${YELLOW}Verifying database schema...${NC}"
if [ ! -f "database/init/01_schema.sql" ]; then
    echo -e "${RED}Error: Database schema file not found${NC}"
    exit 1
fi
echo -e "${GREEN}Database schema verified${NC}"

# Check API health endpoint
echo -e "${YELLOW}Verifying health check endpoint...${NC}"
if ! grep -q "health_check" src/api/main.py; then
    echo -e "${RED}Error: Health check endpoint not found${NC}"
    exit 1
fi
echo -e "${GREEN}Health check endpoint verified${NC}"

# Instructions for manual deployment
echo -e "\n${GREEN}Pre-deployment checks completed successfully!${NC}"
echo -e "\n${YELLOW}To deploy to Render:${NC}"
echo "1. Go to https://dashboard.render.com"
echo "2. Click 'New +' and select 'Web Service'"
echo "3. Connect your GitHub repository"
echo "4. Select the 'healthcare-simulation-api' repository"
echo "5. Render will automatically detect the render.yaml configuration"
echo "6. Click 'Create Web Service'"
echo -e "\n${YELLOW}After deployment:${NC}"
echo "1. Verify the service is running by checking the health endpoint"
echo "2. Monitor the logs for any issues"
echo "3. Set up monitoring alerts"
echo "4. Configure SSL/TLS certificates"
echo -e "\n${GREEN}Your service will be available at: https://healthcare-simulation-api.onrender.com${NC}"
