#!/usr/bin/env python3
"""
CLI tool to check activity between nodes in the healthcare framework.
"""
import argparse
import logging
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeActivityAnalyzer:
    def __init__(self):
        self.log_dir = os.path.join(os.path.dirname(__file__), '../../logs')
        
    def analyze_node_activity(
        self,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        node_types: Optional[List[str]] = None
    ) -> Dict:
        """Analyze activity between nodes."""
        try:
            # Default to last 24 hours if no time range specified
            if not start_time:
                start_time = datetime.now() - timedelta(hours=24)
            if not end_time:
                end_time = datetime.now()
                
            activity_data = {
                "summary": {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "average_response_time": 0.0,
                    "node_activity": {}
                },
                "node_connections": [],
                "timeline": []
            }
            
            # Analyze logs for node activity
            total_response_time = 0
            request_count = 0
            
            for root, _, files in os.walk(self.log_dir):
                for file in files:
                    if file.endswith('.log'):
                        log_path = os.path.join(root, file)
                        with open(log_path, 'r') as f:
                            for line in f:
                                try:
                                    log_entry = json.loads(line)
                                    timestamp = datetime.fromisoformat(log_entry.get('timestamp', ''))
                                    
                                    if start_time <= timestamp <= end_time:
                                        # Process node activity
                                        if 'source_node' in log_entry and 'target_node' in log_entry:
                                            source = log_entry['source_node']
                                            target = log_entry['target_node']
                                            
                                            # Filter by node types if specified
                                            if node_types and not (
                                                any(t in source for t in node_types) or 
                                                any(t in target for t in node_types)
                                            ):
                                                continue
                                                
                                            # Update activity counts
                                            activity_data["summary"]["total_requests"] += 1
                                            if log_entry.get('status') == 'success':
                                                activity_data["summary"]["successful_requests"] += 1
                                            else:
                                                activity_data["summary"]["failed_requests"] += 1
                                                
                                            # Calculate response time
                                            if 'response_time' in log_entry:
                                                total_response_time += float(log_entry['response_time'])
                                                request_count += 1
                                                
                                            # Update node connections
                                            connection = f"{source}->{target}"
                                            activity_data["node_connections"].append({
                                                "source": source,
                                                "target": target,
                                                "timestamp": timestamp.isoformat(),
                                                "status": log_entry.get('status'),
                                                "response_time": log_entry.get('response_time')
                                            })
                                            
                                            # Update node activity counts
                                            for node in [source, target]:
                                                if node not in activity_data["summary"]["node_activity"]:
                                                    activity_data["summary"]["node_activity"][node] = {
                                                        "total_requests": 0,
                                                        "successful_requests": 0,
                                                        "failed_requests": 0
                                                    }
                                                activity_data["summary"]["node_activity"][node]["total_requests"] += 1
                                                if log_entry.get('status') == 'success':
                                                    activity_data["summary"]["node_activity"][node]["successful_requests"] += 1
                                                else:
                                                    activity_data["summary"]["node_activity"][node]["failed_requests"] += 1
                                                    
                                except (json.JSONDecodeError, ValueError) as e:
                                    logger.warning(f"Error processing log entry: {e}")
                                    continue
                                    
            # Calculate average response time
            if request_count > 0:
                activity_data["summary"]["average_response_time"] = total_response_time / request_count
                
            return activity_data
            
        except Exception as e:
            logger.error(f"Error analyzing node activity: {e}")
            return {"error": str(e)}

def main():
    parser = argparse.ArgumentParser(description='Analyze activity between nodes in the healthcare framework')
    parser.add_argument('--start-time', help='Start time for analysis (ISO format)')
    parser.add_argument('--end-time', help='End time for analysis (ISO format)')
    parser.add_argument('--node-types', nargs='+', help='Filter by node types')
    parser.add_argument('--output', help='Output file path for results')
    
    args = parser.parse_args()
    
    try:
        analyzer = NodeActivityAnalyzer()
        
        # Parse time arguments
        start_time = datetime.fromisoformat(args.start_time) if args.start_time else None
        end_time = datetime.fromisoformat(args.end_time) if args.end_time else None
        
        # Analyze activity
        results = analyzer.analyze_node_activity(
            start_time=start_time,
            end_time=end_time,
            node_types=args.node_types
        )
        
        # Output results
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(results, f, indent=2)
            print(f"Results written to {args.output}")
        else:
            print(json.dumps(results, indent=2))
            
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
