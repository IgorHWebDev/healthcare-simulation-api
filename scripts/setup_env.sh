#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Setting up environment variables for Render deployment...${NC}"

# Generate secure random values
generate_secret() {
    openssl rand -base64 32 | tr -d '/+=' | cut -c1-32
}

# Database configuration
export DB_USER="healthcare_$(openssl rand -hex 4)"
export DB_SECRET=$(generate_secret)
export DB_NAME="healthcare_db_$(openssl rand -hex 4)"
export DB_HOST="healthcare-db.render.com"
export DB_PORT="5432"

# Redis configuration
export REDIS_SECRET=$(generate_secret)

# JWT configuration
export JWT_SECRET=$(generate_secret)

# M3 Optimization configuration
export M3_OPTIMIZER_ENABLED="true"
export METAL_FRAMEWORK_ENABLED="true"
export BATCH_SIZE="256"
export MAX_PARALLEL_CIRCUITS="1000"

# Print the configuration (without sensitive values)
echo -e "\n${GREEN}Environment variables set successfully!${NC}"
echo -e "\n${YELLOW}Configuration Summary:${NC}"
echo "DB_USER: ${DB_USER}"
echo "DB_NAME: ${DB_NAME}"
echo "DB_HOST: ${DB_HOST}"
echo "DB_PORT: ${DB_PORT}"
echo "M3_OPTIMIZER_ENABLED: ${M3_OPTIMIZER_ENABLED}"
echo "METAL_FRAMEWORK_ENABLED: ${METAL_FRAMEWORK_ENABLED}"
echo "BATCH_SIZE: ${BATCH_SIZE}"
echo "MAX_PARALLEL_CIRCUITS: ${MAX_PARALLEL_CIRCUITS}"

# Save configuration for Render (excluding sensitive data)
echo -e "\n${YELLOW}Creating Render environment variable configuration...${NC}"
cat > render_env.txt << EOL
# Database Configuration
DB_USER=${DB_USER}
DB_NAME=${DB_NAME}
DB_HOST=${DB_HOST}
DB_PORT=${DB_PORT}

# M3 Optimization
M3_OPTIMIZER_ENABLED=${M3_OPTIMIZER_ENABLED}
METAL_FRAMEWORK_ENABLED=${METAL_FRAMEWORK_ENABLED}
BATCH_SIZE=${BATCH_SIZE}
MAX_PARALLEL_CIRCUITS=${MAX_PARALLEL_CIRCUITS}
EOL

echo -e "\n${GREEN}Configuration saved to render_env.txt${NC}"
echo -e "${YELLOW}IMPORTANT: The following sensitive values have been generated and should be set manually in Render:${NC}"
echo "- DB_SECRET"
echo "- REDIS_SECRET"
echo "- JWT_SECRET"
echo -e "\n${YELLOW}Next steps:${NC}"
echo "1. Copy these values to a secure password manager"
echo "2. Set them in Render's environment variables section"
echo "3. Never commit these values to version control"
echo -e "\n${GREEN}Setup complete! You can now run the deployment script.${NC}"
