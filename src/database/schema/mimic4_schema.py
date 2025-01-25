"""
MIMIC-IV Database Schema Definitions and Data Models.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Patient:
    """Patient information from MIMIC-IV."""
    subject_id: int
    gender: str
    anchor_age: float
    anchor_year: int
    anchor_year_group: str
    dod: Optional[datetime] = None

@dataclass
class Admission:
    """Hospital admission information."""
    hadm_id: int
    subject_id: int
    admittime: datetime
    dischtime: datetime
    admission_type: str
    admission_location: str
    discharge_location: str
    insurance: str
    language: str
    marital_status: str
    ethnicity: str
    hospital_expire_flag: int

@dataclass
class ICUStay:
    """ICU stay information."""
    stay_id: int
    subject_id: int
    hadm_id: int
    first_careunit: str
    last_careunit: str
    intime: datetime
    outtime: datetime
    los: float

@dataclass
class LabEvent:
    """Laboratory test information."""
    labevent_id: int
    subject_id: int
    hadm_id: Optional[int]
    specimen_id: int
    itemid: int
    charttime: datetime
    storetime: datetime
    value: str
    valuenum: Optional[float]
    valueuom: str
    ref_range_lower: Optional[float]
    ref_range_upper: Optional[float]
    flag: Optional[str]
    priority: str
    comments: Optional[str]

@dataclass
class Prescription:
    """Medication prescription information."""
    pharmacy_id: int
    subject_id: int
    hadm_id: int
    starttime: datetime
    stoptime: Optional[datetime]
    drug_type: str
    drug: str
    gsn: Optional[str]
    ndc: Optional[str]
    prod_strength: Optional[str]
    form_rx: Optional[str]
    dose_val_rx: Optional[str]
    dose_unit_rx: Optional[str]
    form_val_disp: Optional[str]
    form_unit_disp: Optional[str]

class MIMIC4Schema:
    """MIMIC-IV database schema manager."""
    
    TABLE_DEFINITIONS = {
        "patients": {
            "subject_id": "INTEGER PRIMARY KEY",
            "gender": "VARCHAR(1)",
            "anchor_age": "INTEGER",
            "anchor_year": "INTEGER",
            "anchor_year_group": "VARCHAR(20)",
            "dod": "TIMESTAMP"
        },
        "admissions": {
            "hadm_id": "INTEGER PRIMARY KEY",
            "subject_id": "INTEGER",
            "admittime": "TIMESTAMP",
            "dischtime": "TIMESTAMP",
            "admission_type": "VARCHAR(40)",
            "admission_location": "VARCHAR(60)",
            "discharge_location": "VARCHAR(60)",
            "insurance": "VARCHAR(255)",
            "language": "VARCHAR(10)",
            "marital_status": "VARCHAR(30)",
            "ethnicity": "VARCHAR(80)",
            "hospital_expire_flag": "SMALLINT"
        },
        "icustays": {
            "stay_id": "INTEGER PRIMARY KEY",
            "subject_id": "INTEGER",
            "hadm_id": "INTEGER",
            "first_careunit": "VARCHAR(20)",
            "last_careunit": "VARCHAR(20)",
            "intime": "TIMESTAMP",
            "outtime": "TIMESTAMP",
            "los": "FLOAT"
        }
    }
    
    FOREIGN_KEYS = {
        "admissions": [
            ("subject_id", "patients", "subject_id")
        ],
        "icustays": [
            ("subject_id", "patients", "subject_id"),
            ("hadm_id", "admissions", "hadm_id")
        ]
    }
    
    @classmethod
    def get_create_table_sql(cls) -> List[str]:
        """Generate SQL statements for table creation."""
        sql_statements = []
        
        for table_name, columns in cls.TABLE_DEFINITIONS.items():
            cols = [f"{col} {dtype}" for col, dtype in columns.items()]
            
            # Add foreign key constraints
            if table_name in cls.FOREIGN_KEYS:
                for col, ref_table, ref_col in cls.FOREIGN_KEYS[table_name]:
                    cols.append(
                        f"FOREIGN KEY ({col}) REFERENCES {ref_table}({ref_col})"
                    )
            
            sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                {', '.join(cols)}
            );
            """
            sql_statements.append(sql)
        
        return sql_statements
    
    @classmethod
    def get_indexes_sql(cls) -> List[str]:
        """Generate SQL statements for index creation."""
        indexes = []
        
        # Add indexes for frequently queried columns
        indexes.extend([
            "CREATE INDEX idx_patient_subject_id ON patients(subject_id);",
            "CREATE INDEX idx_admission_subject_id ON admissions(subject_id);",
            "CREATE INDEX idx_admission_hadm_id ON admissions(hadm_id);",
            "CREATE INDEX idx_icustay_subject_id ON icustays(subject_id);",
            "CREATE INDEX idx_icustay_hadm_id ON icustays(hadm_id);"
        ])
        
        return indexes
