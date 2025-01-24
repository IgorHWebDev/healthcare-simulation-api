from datetime import datetime
from typing import Any
import json

class DateTimeEncoder(json.JSONEncoder):
    """Custom JSON encoder for datetime objects."""
    
    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

def json_dumps(obj: Any) -> str:
    """Serialize object to JSON string with datetime support."""
    return json.dumps(obj, cls=DateTimeEncoder)

def json_loads(s: str) -> Any:
    """Deserialize JSON string to object."""
    return json.loads(s) 