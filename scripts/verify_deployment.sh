#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check environment argument
if [ "$1" != "staging" ] && [ "$1" != "production" ] && [ "$1" != "all" ]; then
    echo -e "${RED}Error: Please specify environment (staging, production, or all)${NC}"
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

# Function to check endpoint health
check_endpoint() {
    local url=$1
    local name=$2
    echo -e "${YELLOW}Checking $name...${NC}"
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url)
    if [ $response -eq 200 ]; then
        echo -e "${GREEN}✓ $name is healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ $name is not healthy (HTTP $response)${NC}"
        return 1
    fi
}

# Function to verify Kubernetes deployment
verify_k8s() {
    local env=$1
    echo -e "${YELLOW}Verifying Kubernetes deployment for $env...${NC}"
    
    # Check pods status
    kubectl get pods -n iqhis-$env | grep -v "Running" | grep -v "Completed" > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${RED}✗ Some pods are not running in $env${NC}"
        kubectl get pods -n iqhis-$env
        return 1
    else
        echo -e "${GREEN}✓ All pods are running in $env${NC}"
    fi
    
    # Check services
    kubectl get services -n iqhis-$env | grep -v "pending" > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All services are running in $env${NC}"
    else
        echo -e "${RED}✗ Some services are pending in $env${NC}"
        kubectl get services -n iqhis-$env
        return 1
    fi
    
    return 0
}

# Function to verify Render deployment
verify_render() {
    local env=$1
    local service_id
    
    if [ "$env" = "production" ]; then
        service_id="prod-healthcare-simulation-api"
    else
        service_id="staging-healthcare-simulation-api"
    fi
    
    echo -e "${YELLOW}Verifying Render deployment for $env...${NC}"
    
    # Check deployment status
    status=$(curl -s -H "Authorization: Bearer $RENDER_API_KEY" \
        "https://api.render.com/v1/services/$service_id/deploys" | \
        jq -r '.[0].status')
    
    if [ "$status" = "live" ]; then
        echo -e "${GREEN}✓ Render deployment is live for $env${NC}"
        return 0
    else
        echo -e "${RED}✗ Render deployment is not live for $env (status: $status)${NC}"
        return 1
    fi
}

# Function to verify a specific environment
verify_environment() {
    local env=$1
    local base_url
    
    if [ "$env" = "production" ]; then
        base_url="https://api.iqhis.com"
    else
        base_url="https://staging.api.iqhis.com"
    fi
    
    echo -e "\n${YELLOW}Starting verification for $env environment...${NC}"
    
    # Verify Kubernetes deployment
    verify_k8s $env
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Verify Render deployment
    verify_render $env
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Check API endpoints
    check_endpoint "$base_url/health" "Health endpoint"
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    check_endpoint "$base_url/quantum/health" "Quantum health endpoint"
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Check metrics endpoint
    check_endpoint "$base_url/metrics" "Metrics endpoint"
    if [ $? -ne 0 ]; then
        return 1
    fi
    
    # Verify Prometheus metrics
    echo -e "${YELLOW}Checking Prometheus metrics...${NC}"
    curl -s "$base_url/metrics" | grep "iqhis_" > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ Prometheus metrics are available${NC}"
    else
        echo -e "${RED}✗ Prometheus metrics are not available${NC}"
        return 1
    fi
    
    # Check logs
    echo -e "${YELLOW}Checking logs...${NC}"
    kubectl logs -n iqhis-$env -l app=iqhis --tail=50 | grep "error" > /dev/null
    if [ $? -eq 0 ]; then
        echo -e "${RED}✗ Found errors in logs${NC}"
        return 1
    else
        echo -e "${GREEN}✓ No errors found in recent logs${NC}"
    fi
    
    echo -e "${GREEN}✓ All checks passed for $env environment${NC}"
    return 0
}

# Main verification logic
if [ "$ENVIRONMENT" = "all" ]; then
    verify_environment "staging"
    staging_result=$?
    
    verify_environment "production"
    prod_result=$?
    
    if [ $staging_result -eq 0 ] && [ $prod_result -eq 0 ]; then
        echo -e "\n${GREEN}✓ All environments verified successfully${NC}"
        exit 0
    else
        echo -e "\n${RED}✗ Verification failed for one or more environments${NC}"
        exit 1
    fi
else
    verify_environment $ENVIRONMENT
    if [ $? -eq 0 ]; then
        echo -e "\n${GREEN}✓ Environment $ENVIRONMENT verified successfully${NC}"
        exit 0
    else
        echo -e "\n${RED}✗ Verification failed for environment $ENVIRONMENT${NC}"
        exit 1
    fi
fi 