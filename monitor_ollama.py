#!/usr/bin/env python3
import asyncio
import aiohttp
import json
import datetime
import sys
import os

async def monitor_api_endpoints():
    # API endpoints that use Ollama
    endpoints = [
        "http://localhost:8000/v1/healthcare/simulate",
        "http://localhost:8000/v1/healthcare/validate"
    ]
    
    # Test simulation request
    simulation_data = {
        "scenario": "Patient presenting with chest pain",
        "title": "Chest Pain Assessment",
        "actors": ["Paramedic", "Patient"],
        "steps": [
            {
                "step": 1,
                "description": "Initial Assessment",
                "actions": [
                    {
                        "action": "Check vital signs",
                        "details": "Measure BP, pulse, respiration",
                        "references": ["ACLS Protocol 2023"]
                    }
                ]
            }
        ]
    }

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                # Test simulation endpoint
                print(f"\n[{datetime.datetime.now()}] Testing simulation endpoint...")
                async with session.post(
                    endpoints[0],
                    json=simulation_data,
                    headers={"X-API-Key": "rnd_HLkUlkx4xrvVnbXQ8Q0NHr5ffIe1"}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        print(f"✓ Simulation endpoint responded successfully")
                        print(f"Response: {json.dumps(data, indent=2)}")
                    else:
                        print(f"✗ Simulation endpoint error: {response.status}")
                
                # Check Ollama status
                print(f"\n[{datetime.datetime.now()}] Checking Ollama status...")
                async with session.get("http://localhost:11434/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = [model["name"] for model in data.get("models", [])]
                        print(f"✓ Ollama is running with models: {', '.join(models)}")
                    else:
                        print(f"✗ Ollama error: {response.status}")
                
            except aiohttp.ClientError as e:
                print(f"Connection error: {str(e)}")
            except Exception as e:
                print(f"Error: {str(e)}")
            
            await asyncio.sleep(10)  # Wait 10 seconds before next check

if __name__ == "__main__":
    print("Starting API endpoint monitoring...")
    try:
        asyncio.run(monitor_api_endpoints())
    except KeyboardInterrupt:
        print("\nMonitoring stopped by user")
        sys.exit(0)
