# Custom GPT Example Prompts for IQHIS Integration

## Overview
This document provides example prompts and expected interactions for the Custom GPT integration with IQHIS, demonstrating various use cases and API interactions.

## 1. Basic Health Record Encryption

### User Prompt
```
Encrypt this health record:
Patient ID: 12345
Diagnosis: Type 2 Diabetes
Medication: Metformin 500mg
Blood Pressure: 130/85
```

### Expected GPT Response
```
I'll help you encrypt this health record using the IQHIS quantum-safe encryption.

API Call:
POST /quantum/encrypt
{
    "data": {
        "patient_id": "12345",
        "diagnosis": "Type 2 Diabetes",
        "medication": "Metformin 500mg",
        "vitals": {
            "blood_pressure": "130/85"
        }
    }
}

Response:
{
    "encrypted_data": "<encrypted_string>",
    "key_id": "qk_2024_03_21_abc123",
    "expires_at": "2024-03-22T10:00:00Z",
    "performance_metrics": {
        "encryption_time_ms": 150,
        "key_strength": "256-bit"
    }
}

Your health record has been encrypted using quantum-safe encryption. The encrypted data and key ID have been generated. The encryption will expire in 24 hours.
```

## 2. System Health Check

### User Prompt
```
Check if the IQHIS system is healthy and ready for encryption operations.
```

### Expected GPT Response
```
I'll check the health status of the IQHIS system.

API Call:
GET /quantum/health

Response:
{
    "status": "healthy",
    "last_key_rotation": "2024-03-21T08:00:00Z",
    "current_load": 0.3,
    "quantum_metrics": {
        "key_strength": "256-bit",
        "active_sessions": 5
    }
}

The IQHIS system is healthy and operating normally. The last key rotation was performed at 08:00:00 UTC, and the system is under normal load (30% capacity). The quantum encryption system is using 256-bit key strength with 5 active sessions.
```

## 3. Batch Health Records Encryption

### User Prompt
```
Encrypt these lab results for multiple patients:
1. Patient 12345: Glucose 126 mg/dL
2. Patient 67890: Cholesterol 200 mg/dL
3. Patient 11111: HbA1c 7.1%
```

### Expected GPT Response
```
I'll help you encrypt multiple lab results using batch processing.

API Call:
POST /quantum/encrypt
{
    "data": {
        "lab_results": [
            {
                "patient_id": "12345",
                "test": "Glucose",
                "value": "126",
                "unit": "mg/dL"
            },
            {
                "patient_id": "67890",
                "test": "Cholesterol",
                "value": "200",
                "unit": "mg/dL"
            },
            {
                "patient_id": "11111",
                "test": "HbA1c",
                "value": "7.1",
                "unit": "%"
            }
        ]
    }
}

Response:
{
    "encrypted_data": "<encrypted_string>",
    "key_id": "qk_2024_03_21_def456",
    "expires_at": "2024-03-22T10:00:00Z",
    "performance_metrics": {
        "encryption_time_ms": 250,
        "key_strength": "256-bit",
        "batch_size": 3
    }
}

The lab results have been encrypted using quantum-safe encryption. A single encrypted payload has been generated for all records, with a unique key ID for access control.
```

## 4. Error Handling Example

### User Prompt
```
Encrypt this invalid health record:
Patient: {malformed_data}
```

### Expected GPT Response
```
I attempted to encrypt the health record, but encountered an error.

API Call:
POST /quantum/encrypt
{
    "data": {
        "patient": "{malformed_data}"
    }
}

Response:
{
    "error": {
        "code": "INVALID_DATA_FORMAT",
        "message": "The provided health record data is not properly formatted",
        "details": "Patient data must be a valid JSON object with required fields"
    }
}

I apologize, but I cannot encrypt this health record because the data is malformed. Please ensure the health record contains valid patient information in a proper format. Here's an example of the correct format:

{
    "patient_id": "12345",
    "record_type": "clinical_note",
    "content": "Patient visit details..."
}
```

## 5. Compliance Check Example

### User Prompt
```
Verify if this data is compliant for encryption:
SSN: 123-45-6789
Credit Card: 4111-1111-1111-1111
Medical Record: Patient has hypertension
```

### Expected GPT Response
```
I'll help you verify the compliance of this data before encryption.

Warning: I notice that this data contains sensitive information (SSN and credit card number) that should not be transmitted. I will only process the medical record portion in compliance with HIPAA regulations.

API Call:
POST /quantum/encrypt
{
    "data": {
        "medical_record": "Patient has hypertension"
    }
}

Response:
{
    "encrypted_data": "<encrypted_string>",
    "key_id": "qk_2024_03_21_ghi789",
    "expires_at": "2024-03-22T10:00:00Z",
    "compliance_check": {
        "phi_detected": true,
        "encryption_level": "HIPAA-compliant",
        "audit_trail": "enabled"
    }
}

I've encrypted only the medical record information. The SSN and credit card number were excluded as they should be handled by different security systems. The encryption used is HIPAA-compliant and includes an audit trail.
```

## Best Practices

1. Always validate data format before sending to the API
2. Handle sensitive information appropriately
3. Check system health before large batch operations
4. Monitor encryption performance metrics
5. Maintain proper error handling
6. Ensure HIPAA compliance in all operations

## References

- IQHIS API Documentation
- HIPAA Compliance Guidelines
- Quantum Encryption Best Practices
- Error Handling Documentation 