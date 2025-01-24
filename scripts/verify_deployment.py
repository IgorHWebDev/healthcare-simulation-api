#!/usr/bin/env python3
"""
Deployment verification script for Healthcare Simulation API.
Tests endpoints and integration after deployment.
"""

import requests
import sys
import json
from typing import Dict, Any
import logging
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DeploymentVerifier:
    """Verifies deployment and endpoint functionality."""
    
    def __init__(self, base_url: str, api_key: str):
        """Initialize verifier with API details."""
        self.base_url = base_url.rstrip('/')
        self.headers = {
            'X-RapidAPI-Key': api_key,
            'Content-Type': 'application/json'
        }
        
    def verify_health(self) -> bool:
        """Verify health check endpoint."""
        try:
            response = requests.get(f"{self.base_url}/health")
            assert response.status_code == 200
            assert response.json()['status'] == 'ok'
            logger.info("✅ Health check passed")
            return True
        except Exception as e:
            logger.error(f"❌ Health check failed: {str(e)}")
            return False
            
    def verify_simulation(self) -> bool:
        """Verify simulation endpoint."""
        try:
            payload = {
                "message": "Start cardiac arrest simulation",
                "language": "en"
            }
            response = requests.post(
                f"{self.base_url}/simulate",
                headers=self.headers,
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert all(k in data for k in ['scenario_id', 'response', 'next_steps'])
            logger.info("✅ Simulation endpoint verified")
            return True
        except Exception as e:
            logger.error(f"❌ Simulation endpoint failed: {str(e)}")
            return False
            
    def verify_validation(self) -> bool:
        """Verify validation endpoint."""
        try:
            payload = {
                "action": "Start chest compressions",
                "protocol": "ACLS"
            }
            response = requests.post(
                f"{self.base_url}/validate",
                headers=self.headers,
                json=payload
            )
            assert response.status_code == 200
            data = response.json()
            assert all(k in data for k in ['is_valid', 'feedback', 'score'])
            logger.info("✅ Validation endpoint verified")
            return True
        except Exception as e:
            logger.error(f"❌ Validation endpoint failed: {str(e)}")
            return False
            
    def verify_all(self) -> bool:
        """Run all verifications."""
        results = [
            self.verify_health(),
            self.verify_simulation(),
            self.verify_validation()
        ]
        success = all(results)
        if success:
            logger.info("✅ All verifications passed")
        else:
            logger.error("❌ Some verifications failed")
        return success

def main():
    """Main entry point."""
    if len(sys.argv) != 3:
        print("Usage: verify_deployment.py <base_url> <api_key>")
        sys.exit(1)
        
    base_url = sys.argv[1]
    api_key = sys.argv[2]
    
    verifier = DeploymentVerifier(base_url, api_key)
    success = verifier.verify_all()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 