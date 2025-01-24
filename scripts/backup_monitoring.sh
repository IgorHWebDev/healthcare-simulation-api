#!/bin/bash

# Configuration
BACKUP_DIR="backups/monitoring"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_DIR}/${TIMESTAMP}"

# Create backup directories
mkdir -p "${BACKUP_PATH}"

# Backup monitoring configurations
echo "Backing up monitoring configurations..."
cp monitoring/prometheus.yml "${BACKUP_PATH}/"
cp monitoring/alert_rules.yml "${BACKUP_PATH}/"
cp -r monitoring/grafana "${BACKUP_PATH}/"

# Create manifest file
cat > "${BACKUP_PATH}/MANIFEST.md" << EOF
# Monitoring Configuration Backup

## Backup Information
- Date: $(date)
- Timestamp: ${TIMESTAMP}

## Files Included
- prometheus.yml
- alert_rules.yml
- grafana/dashboards/

## Configuration State
- Prometheus Version: $(docker exec iqhis-prometheus prometheus --version 2>/dev/null || echo "Not running")
- Grafana Version: $(docker exec iqhis-grafana grafana-server -v 2>/dev/null || echo "Not running")

## Service Status
- Prometheus: $(docker ps -q -f name=iqhis-prometheus >/dev/null 2>&1 && echo "Running" || echo "Not running")
- Grafana: $(docker ps -q -f name=iqhis-grafana >/dev/null 2>&1 && echo "Running" || echo "Not running")

## Alert Rules
$(grep "alert:" monitoring/alert_rules.yml | sed 's/^/- /')

## Notes
- Manual backup created during monitoring setup
- Includes all current alert rules and dashboards
- Backup created as part of Sprint 0 preparation
EOF

# Create archive
cd "${BACKUP_DIR}" && tar -czf "${TIMESTAMP}.tar.gz" "${TIMESTAMP}"
rm -rf "${TIMESTAMP}"

echo "Backup completed: ${BACKUP_DIR}/${TIMESTAMP}.tar.gz"
echo "Manifest created: ${BACKUP_DIR}/${TIMESTAMP}/MANIFEST.md" 