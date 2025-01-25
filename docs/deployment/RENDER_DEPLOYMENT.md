# Render Deployment Guide

## Overview
This guide explains how to deploy the Healthcare Simulation API to Render with proper security measures and M3 optimization.

## Prerequisites
- Render account with appropriate permissions
- PostgreSQL database service
- Redis cache service
- Environment variables configured

## Security Measures
1. **Environment Variables**
   - Never commit sensitive data to version control
   - Use Render's environment variable management
   - Rotate secrets regularly

2. **Database Security**
   - Use strong, unique secrets
   - Enable SSL/TLS connections
   - Implement connection pooling
   - Regular security audits

3. **API Security**
   - JWT authentication
   - Rate limiting
   - IP allowlisting
   - Regular security updates

## Deployment Steps

### 1. Database Setup
```bash
# Create PostgreSQL service on Render
render db create \
  --name healthcare-db \
  --plan standard \
  --region $REGION \
  --user $DB_USER
```

### 2. Environment Variables
Required variables in Render dashboard:
```
DB_USER=<database_user>
DB_SECRET=<database_secret>
DB_NAME=<database_name>
DB_HOST=<database_host>
DB_PORT=<database_port>
REDIS_SECRET=<redis_secret>
JWT_SECRET=<jwt_secret>
M3_OPTIMIZER_ENABLED=true
METAL_FRAMEWORK_ENABLED=true
```

### 3. Deploy API Service
```bash
# Deploy web service
render deploy \
  --name healthcare-simulation-api \
  --plan standard \
  --region $REGION \
  --branch main
```

## M3 Optimization Configuration

### Metal Framework Settings
```yaml
M3_OPTIMIZER_ENABLED: true
METAL_FRAMEWORK_ENABLED: true
BATCH_SIZE: 256
MAX_PARALLEL_CIRCUITS: 1000
```

### Performance Tuning
- Adjust `BATCH_SIZE` based on load
- Monitor Metal framework utilization
- Optimize database queries
- Configure connection pooling

## Health Monitoring

### Endpoints
- `/api/v1/health`: Basic health check
- `/api/v1/status`: Detailed system status

### Metrics
- Database connection status
- M3 optimizer performance
- API response times
- Error rates

## Troubleshooting

### Common Issues
1. Database Connection
   ```bash
   # Check database connectivity
   render db ping healthcare-db
   ```

2. M3 Optimizer
   ```bash
   # Verify Metal framework status
   render logs healthcare-simulation-api --filter "metal"
   ```

3. Performance Issues
   ```bash
   # Monitor resource usage
   render metrics healthcare-simulation-api
   ```

## Security Best Practices

### Regular Maintenance
1. Update dependencies monthly
2. Rotate secrets quarterly
3. Review access logs weekly
4. Perform security audits

### Access Control
1. Implement role-based access
2. Use short-lived tokens
3. Monitor failed authentication attempts
4. Implement IP allowlisting

## Backup and Recovery

### Database Backups
```bash
# Configure automated backups
render db backup-schedule healthcare-db \
  --retention 7 \
  --frequency daily
```

### Disaster Recovery
1. Maintain backup strategy
2. Document recovery procedures
3. Test recovery regularly
4. Keep deployment artifacts
