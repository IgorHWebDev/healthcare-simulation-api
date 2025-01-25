#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

# Check environment argument
if [ "$1" != "staging" ] && [ "$1" != "production" ]; then
    echo -e "${RED}Error: Please specify environment (staging or production)${NC}"
    exit 1
fi

ENVIRONMENT=$1

# Load environment variables
if [ -f .env ]; then
    source .env
else
    echo -e "${RED}Error: .env file not found${NC}"
    exit 1
fi

# Verify prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}Error: docker is required but not installed${NC}" >&2; exit 1; }
command -v kubectl >/dev/null 2>&1 || { echo -e "${RED}Error: kubectl is required but not installed${NC}" >&2; exit 1; }
command -v helm >/dev/null 2>&1 || { echo -e "${RED}Error: helm is required but not installed${NC}" >&2; exit 1; }

echo -e "${GREEN}Starting deployment to $ENVIRONMENT...${NC}"

# Run tests
echo "Running tests..."
if ! pytest tests/; then
    echo -e "${RED}Error: Tests failed${NC}"
    exit 1
fi

# Build and push Docker image
echo "Building Docker image..."
VERSION=$(cat VERSION)
IMAGE_NAME="iqhis/api:$VERSION-$ENVIRONMENT"

if ! docker build -t $IMAGE_NAME .; then
    echo -e "${RED}Error: Docker build failed${NC}"
    exit 1
fi

echo "Pushing Docker image..."
if ! docker push $IMAGE_NAME; then
    echo -e "${RED}Error: Docker push failed${NC}"
    exit 1
fi

# Deploy to Render
echo "Deploying to Render..."
if [ "$ENVIRONMENT" = "production" ]; then
    RENDER_SERVICE="prod-healthcare-simulation-api"
else
    RENDER_SERVICE="staging-healthcare-simulation-api"
fi

curl -X POST "https://api.render.com/v1/services/$RENDER_SERVICE/deploys" \
  -H "Authorization: Bearer $RENDER_API_KEY" \
  -H "Content-Type: application/json"

# Deploy Kubernetes resources
echo "Deploying Kubernetes resources..."
kubectl config use-context $ENVIRONMENT

# Update Helm charts
echo "Updating Helm charts..."
helm dependency update ./helm

# Deploy with Helm
if ! helm upgrade --install iqhis ./helm \
    --namespace iqhis-$ENVIRONMENT \
    --create-namespace \
    --set environment=$ENVIRONMENT \
    --set image.tag=$VERSION-$ENVIRONMENT \
    --values ./helm/values-$ENVIRONMENT.yaml; then
    echo -e "${RED}Error: Helm deployment failed${NC}"
    exit 1
fi

# Verify deployment
echo "Verifying deployment..."
./scripts/verify_deployment.sh $ENVIRONMENT

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Deployment to $ENVIRONMENT completed successfully!${NC}"
    echo -e "Monitor deployment status at: https://dashboard.render.com/web/$RENDER_SERVICE"
else
    echo -e "${RED}Deployment verification failed${NC}"
    exit 1
fi

# Update documentation
echo "Updating deployment documentation..."
if [ "$ENVIRONMENT" = "production" ]; then
    echo "$(date): Deployed version $VERSION to production" >> docs/deployment/CHANGELOG.md
fi

exit 0 