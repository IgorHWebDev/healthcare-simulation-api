from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import json
import logging
from pathlib import Path
from api.healthcare.models import AuditLogEntry, AuditQuery
import os

class AuditLogger:
    """
    Audit logger for tracking PHI access and operations.
    """
    
    def __init__(self):
        """Initialize audit logger with file storage."""
        self.log_dir = Path("logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure logger
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        self.log_file = self.log_dir / "audit.log"
        handler = logging.FileHandler(str(self.log_file))
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", %(message)s}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    async def log_access(
        self,
        user_id: str,
        patient_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log an access event."""
        try:
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "user_id": user_id,
                "patient_id": patient_id,
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "details": details or {}
            }
            
            log_file = self.log_dir / f"{patient_id}.log"
            with open(log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
        except Exception as e:
            print(f"Error logging access: {str(e)}")
    
    async def get_logs(
        self,
        patient_id: Optional[str] = None,
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get audit logs with optional filtering."""
        logs = []
        try:
            if patient_id:
                log_file = self.log_dir / f"{patient_id}.log"
                if log_file.exists():
                    with open(log_file, "r") as f:
                        for line in f:
                            log = json.loads(line)
                            if self._matches_filters(log, action, start_date, end_date):
                                logs.append(log)
            else:
                for log_file in self.log_dir.glob("*.log"):
                    with open(log_file, "r") as f:
                        for line in f:
                            log = json.loads(line)
                            if self._matches_filters(log, action, start_date, end_date):
                                logs.append(log)
        except Exception as e:
            print(f"Error retrieving logs: {str(e)}")
            return []
        
        return logs
    
    def _matches_filters(
        self,
        log: Dict[str, Any],
        action: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> bool:
        """Check if a log entry matches the given filters."""
        if action and log["action"] != action:
            return False
        
        if start_date or end_date:
            log_date = datetime.fromisoformat(log["timestamp"])
            if start_date and log_date < start_date:
                return False
            if end_date and log_date > end_date:
                return False
        
        return True
    
    async def export_logs(
        self,
        output_path: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs to a file.
        """
        logs = await self.get_logs(start_date=start_date, end_date=end_date)
        
        output_file = Path(output_path)
        with open(output_file, "w") as f:
            json.dump(logs, f, indent=2)
            
        return str(output_file)
    
    def clear_logs(self) -> None:
        """Clear all audit logs."""
        try:
            for log_file in self.log_dir.glob("*.log"):
                log_file.unlink()
        except Exception as e:
            print(f"Error clearing logs: {str(e)}")
            return
            
        # Reset logger handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
            
        # Add new file handler
        handler = logging.FileHandler(str(self.log_file))
        formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", %(message)s}'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler) 