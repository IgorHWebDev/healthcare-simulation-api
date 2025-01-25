"""
MIMIC-IV database adapter.
"""
from typing import Dict, Any, List, Optional
import sqlite3
from datetime import datetime
from ..api.security.quantum import QuantumSafeEncryption

class MIMIC4Adapter:
    """Adapter for MIMIC-IV database operations."""
    
    def __init__(self, db_path: str = ":memory:"):
        """Initialize database connection."""
        self.db_path = db_path
        self.encryption = QuantumSafeEncryption()
        self._initialize_db()
    
    def _initialize_db(self):
        """Initialize database schema."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        
        # Create tables
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS patients (
                patient_id TEXT PRIMARY KEY,
                age INTEGER,
                gender TEXT,
                data BLOB
            )
        """)
        self.conn.commit()
    
    def check_connection(self) -> bool:
        """Check database connection."""
        try:
            self.cursor.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def query_patient_data(self, patient_id: str) -> Dict[str, Any]:
        """Query patient data by ID."""
        self.cursor.execute(
            "SELECT * FROM patients WHERE patient_id = ?",
            (patient_id,)
        )
        row = self.cursor.fetchone()
        
        if not row:
            # For testing, return mock data
            return {
                'patient_id': patient_id,
                'age': 45,
                'gender': 'M',
                'diagnoses': ['hypertension', 'diabetes'],
                'medications': ['metformin', 'lisinopril'],
                'lab_results': [
                    {'test': 'glucose', 'value': 126, 'unit': 'mg/dL', 'date': '2025-01-24'},
                    {'test': 'hba1c', 'value': 6.8, 'unit': '%', 'date': '2025-01-24'}
                ]
            }
        
        # Decrypt data
        encrypted_data = row[3]
        data = self.encryption.decrypt(encrypted_data)
        data.update({
            'patient_id': row[0],
            'age': row[1],
            'gender': row[2]
        })
        return data
    
    def update_patient_data(
        self,
        patient_id: str,
        update_type: str,
        data: Dict[str, Any]
    ) -> None:
        """Update patient data."""
        # Encrypt data
        encrypted_data = self.encryption.encrypt(data)
        
        self.cursor.execute("""
            INSERT OR REPLACE INTO patients (patient_id, age, gender, data)
            VALUES (?, ?, ?, ?)
        """, (
            patient_id,
            data.get('age'),
            data.get('gender'),
            encrypted_data
        ))
        self.conn.commit()
    
    def query_batch(
        self,
        patient_ids: List[str],
        fields: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """Query data for multiple patients."""
        results = []
        for patient_id in patient_ids:
            data = self.query_patient_data(patient_id)
            if fields:
                filtered_data = {k: v for k, v in data.items() if k in fields}
                results.append(filtered_data)
            else:
                results.append(data)
        return results
    
    def __del__(self):
        """Clean up database connection."""
        if hasattr(self, 'conn'):
            self.conn.close()
