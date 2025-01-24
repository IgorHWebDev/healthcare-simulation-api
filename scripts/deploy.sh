#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 Starting deployment process..."

# Check if git is clean
if [[ -n $(git status -s) ]]; then
    echo -e "${RED}Error: You have uncommitted changes${NC}"
    echo "Please commit or stash your changes before deploying"
    exit 1
fi

# Push to GitHub
echo "📤 Pushing to GitHub..."
git push origin master

# Deploy to Render
echo "🔄 Deploying to Render..."
curl -s -X POST \
    -H "Authorization: Bearer $RENDER_API_KEY" \
    -H "Content-Type: application/json" \
    "https://api.render.com/v1/services/$RENDER_SERVICE_ID/deploys"

echo -e "\n${GREEN}✅ Deployment triggered successfully!${NC}"
echo "You can monitor the deployment status at: https://dashboard.render.com/web/srv-$RENDER_SERVICE_ID" 