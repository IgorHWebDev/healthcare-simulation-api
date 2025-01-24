# Healthcare Endpoints Technical Specification

## Overview
This document provides technical specifications for the healthcare-specific endpoints in the IQHIS system.

## Version Information
- Version: 0.1.0-sprint.1
- Status: Implementation
- Last Updated: 2024-03-21

## 1. PHI Handling Endpoints

### 1.1 Store PHI
**Endpoint**: `/v1/healthcare/phi/store`
**Method**: POST
```python
class PHIData(BaseModel):
    patient_id: str = Field(..., pattern="^P\d{10}$")
    data_type: str = Field(..., enum=["demographics", "medical_history", "lab_results"])
    content: Dict[str, Any]
    metadata: Optional[Dict[str, str]] = None

class PHIResponse(BaseModel):
    record_id: str
    timestamp: datetime
    status: str
```

### 1.2 Retrieve PHI
**Endpoint**: `/v1/healthcare/phi/retrieve`
**Method**: GET
```python
class PHIQuery(BaseModel):
    patient_id: str = Field(..., pattern="^P\d{10}$")
    data_type: Optional[str] = Field(None, enum=["demographics", "medical_history", "lab_results"])
    record_id: Optional[str] = None
```

### 1.3 Audit PHI Access
**Endpoint**: `/v1/healthcare/phi/audit`
**Method**: GET
```python
class AuditQuery(BaseModel):
    patient_id: Optional[str] = Field(None, pattern="^P\d{10}$")
    start_date: datetime
    end_date: datetime
    access_type: Optional[str] = Field(None, enum=["read", "write", "delete"])
```

## 2. DICOM Integration

### 2.1 Store DICOM
**Endpoint**: `/v1/healthcare/dicom/store`
**Method**: POST
```python
class DICOMData(BaseModel):
    patient_id: str = Field(..., pattern="^P\d{10}$")
    study_uid: str
    series_uid: str
    image_data: bytes
    metadata: Dict[str, Any]

class DICOMResponse(BaseModel):
    image_id: str
    study_uid: str
    series_uid: str
    status: str
```

### 2.2 Retrieve DICOM
**Endpoint**: `/v1/healthcare/dicom/retrieve`
**Method**: GET
```python
class DICOMQuery(BaseModel):
    patient_id: str = Field(..., pattern="^P\d{10}$")
    study_uid: Optional[str] = None
    series_uid: Optional[str] = None
    image_id: Optional[str] = None
```

### 2.3 DICOM Metadata
**Endpoint**: `/v1/healthcare/dicom/metadata`
**Method**: GET
```python
class MetadataQuery(BaseModel):
    image_id: str
    include_private_tags: bool = False
```

## 3. HL7 FHIR Integration

### 3.1 Patient Resource
**Endpoint**: `/v1/healthcare/fhir/patient`
**Method**: POST, GET, PUT
```python
class PatientResource(BaseModel):
    identifier: List[Dict[str, str]]
    active: bool
    name: List[Dict[str, str]]
    telecom: Optional[List[Dict[str, str]]]
    gender: str = Field(..., enum=["male", "female", "other", "unknown"])
    birthDate: str
    address: Optional[List[Dict[str, str]]]
```

### 3.2 Observation Resource
**Endpoint**: `/v1/healthcare/fhir/observation`
**Method**: POST, GET
```python
class ObservationResource(BaseModel):
    identifier: List[Dict[str, str]]
    status: str = Field(..., enum=["registered", "preliminary", "final", "amended"])
    category: List[Dict[str, str]]
    code: Dict[str, Any]
    subject: Dict[str, str]
    effectiveDateTime: str
    value: Dict[str, Any]
```

### 3.3 Diagnostic Report
**Endpoint**: `/v1/healthcare/fhir/diagnostic`
**Method**: POST, GET
```python
class DiagnosticReport(BaseModel):
    identifier: List[Dict[str, str]]
    status: str
    category: Dict[str, Any]
    code: Dict[str, Any]
    subject: Dict[str, str]
    effectiveDateTime: str
    issued: str
    performer: List[Dict[str, str]]
    result: List[Dict[str, str]]
```

## Security Requirements

### Authentication
- All endpoints require JWT authentication
- Token must include appropriate role and permissions
- Access tokens expire after 1 hour

### Authorization
- Role-based access control (RBAC)
- Department-level access restrictions
- Patient-specific access controls

### Encryption
- All PHI data encrypted at rest using quantum-resistant encryption
- TLS 1.3 for data in transit
- Key rotation every 24 hours

## Performance Requirements

### Response Times
- PHI endpoints: < 200ms
- DICOM endpoints: < 500ms
- FHIR endpoints: < 300ms

### Throughput
- Minimum 100 requests/second per endpoint
- Burst capacity up to 500 requests/second

### Availability
- 99.99% uptime requirement
- Automatic failover
- Load balancing across multiple instances

## Error Handling

### Standard Error Responses
```python
class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: Optional[Dict[str, Any]]
    timestamp: datetime
```

### Error Categories
1. Authentication Errors (401)
2. Authorization Errors (403)
3. Validation Errors (422)
4. Resource Errors (404)
5. Server Errors (500)

## Monitoring

### Metrics Collection
- Request/response times
- Error rates
- Resource utilization
- Security events

### Alerts
- Response time thresholds
- Error rate thresholds
- Security incident alerts
- Resource utilization alerts

## Testing Requirements

### Unit Tests
- Input validation
- Error handling
- Security controls
- Data transformation

### Integration Tests
- End-to-end workflows
- Security integration
- Performance testing
- Compliance validation

## References
- HIPAA Security Rule
- DICOM Standard (PS3)
- HL7 FHIR R4
- NIST Security Guidelines 