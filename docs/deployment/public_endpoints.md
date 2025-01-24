# Public Endpoint Deployment Guide

## Overview
This document outlines the deployment process for IQHIS public endpoints following the Hybrid Agile-Waterfall methodology.

## Version Information
- Version: 0.1.0-sprint.0
- Status: Production
- Last Updated: 2024-03-21

## Prerequisites
- Domain name configured for api.iqhis.com
- SSL certificates (Let's Encrypt)
- Nginx installed
- Prometheus and monitoring tools
- UFW firewall

## Security Configurations

### 1. SSL/TLS Setup
- TLS 1.3 only
- HSTS enabled
- OCSP stapling
- Session security optimized

### 2. Authentication
- JWT-based authentication
- Public key infrastructure
- Token validation at Nginx level

### 3. Rate Limiting
- Global: 120 requests/minute
- Burst: 20 requests
- Auth endpoints: 5 requests/second

### 4. CORS Policy
- Production origins only
- Strict method limitations
- Secure header configurations

## Monitoring Setup

### 1. Metrics Collection
- API metrics via Prometheus
- Node metrics via node_exporter
- Nginx metrics via nginx-prometheus-exporter

### 2. Alert Configuration
- Response time thresholds
- Error rate monitoring
- Security incident alerts
- Resource utilization warnings

## Deployment Process

### 1. Initial Setup
```bash
# Clone repository
git clone https://github.com/your-org/iqhis.git
cd iqhis

# Set up environment
cp .env.example .env
nano .env  # Configure environment variables
```

### 2. SSL Certificate Installation
```bash
# Run certbot
sudo ./scripts/deploy_public.sh
```

### 3. Configuration Deployment
- Nginx configuration at `/etc/nginx/conf.d/iqhis.conf`
- Prometheus configuration at `/etc/prometheus/prometheus.yml`
- Security configurations in `/etc/nginx/security/`

### 4. Verification Steps
1. Check SSL setup
2. Verify rate limiting
3. Test CORS policies
4. Validate monitoring
5. Confirm security headers

## Endpoints

### Public Endpoints
- `GET /v1/quantum/health`
  - No authentication required
  - Rate limited: 120/minute
  - CORS: Allow all origins

### Protected Endpoints
- `POST /v1/quantum/encrypt`
  - Requires JWT authentication
  - Rate limited: 120/minute
  - CORS: Production origins only

- `GET /v1/metrics`
  - Requires JWT authentication
  - Rate limited: 120/minute
  - CORS: Production origins only

## Monitoring

### 1. Available Metrics
- Response times
- Error rates
- Resource utilization
- Security events
- Rate limit hits

### 2. Dashboards
- System health
- API performance
- Security monitoring
- Resource utilization

## Troubleshooting

### Common Issues
1. SSL Certificate Problems
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

2. Rate Limiting Issues
   ```bash
   sudo tail -f /var/log/nginx/error.log
   ```

3. Monitoring Problems
   ```bash
   sudo systemctl status prometheus
   sudo systemctl status node_exporter
   ```

## Maintenance

### Regular Tasks
1. SSL certificate renewal (automated)
2. Security updates
3. Performance monitoring
4. Log rotation

### Emergency Procedures
1. Incident response plan
2. Rollback procedures
3. Emergency contacts

## Compliance

### HIPAA Requirements
- Encryption in transit
- Access controls
- Audit logging
- Incident response

### Security Standards
- NIST guidelines
- OWASP security practices
- Healthcare industry standards

## Support

### Contact Information
- Technical Support: support@iqhis.com
- Security Team: security@iqhis.com
- Emergency: oncall@iqhis.com 