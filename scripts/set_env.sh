#!/bin/bash

# Generate secure random values
generate_secret() {
    openssl rand -base64 32 | tr -d '/+=' | cut -c1-32
}

# Export environment variables
export RENDER_API_KEY=""  # Replace with your Render API key
export API_KEY=$(generate_secret)
export DB_USER="healthcare_d5178a2d"
export DB_NAME="healthcare_db_70b129a4"
export DB_SECRET=$(generate_secret)
export REDIS_SECRET=$(generate_secret)
export JWT_SECRET=$(generate_secret)

echo "Environment variables set successfully!"
echo "Note: Replace RENDER_API_KEY with your actual Render API key"
