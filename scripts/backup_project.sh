#!/bin/bash

# Script to backup IQHIS project state
# Creates a timestamped backup of all project files

# Set variables
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/iqhis_backup_${TIMESTAMP}"
BACKUP_MANIFEST="${BACKUP_DIR}/MANIFEST.md"
ARCHIVE_NAME="iqhis_backup_${TIMESTAMP}.tar.gz"

# Create backup directory
mkdir -p "${BACKUP_DIR}"

# Copy project files
echo "Copying project files..."
cp -r agents "${BACKUP_DIR}/"
cp -r config "${BACKUP_DIR}/"
cp -r docs "${BACKUP_DIR}/"
cp -r docker "${BACKUP_DIR}/"
cp -r scripts "${BACKUP_DIR}/"
cp requirements.txt "${BACKUP_DIR}/"

# Create manifest
echo "Creating backup manifest..."
cat > "${BACKUP_MANIFEST}" << EOF
# IQHIS Project Backup Manifest
Generated: $(date)

## Backup Information
- Timestamp: ${TIMESTAMP}
- Location: ${BACKUP_DIR}
- Archive: ${ARCHIVE_NAME}

## Files Included
$(find "${BACKUP_DIR}" -type f -not -name "MANIFEST.md" | sed 's|'${BACKUP_DIR}'/||' | sed 's/^/- /')

## Environment State
- OS: $(uname -a)
- Docker: $(docker --version)
- Docker Compose: $(docker-compose --version)

## Configuration State
- Quantum Agent Config: Present
- Docker Compose Config: Present
- Environment Validation: In Progress

## Service Status
$(docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Health}}" 2>/dev/null || echo "No services running")

## Notes
- Backup includes all source code, configuration, and documentation
- Environment validation is in progress
- Docker infrastructure is configured but not all services are validated
EOF

# Create archive
echo "Creating backup archive..."
tar -czf "${ARCHIVE_NAME}" -C backups "iqhis_backup_${TIMESTAMP}"

# Cleanup
echo "Cleaning up temporary files..."
rm -rf "${BACKUP_DIR}"

echo "Backup completed successfully!"
echo "Backup archive: ${ARCHIVE_NAME}"
echo "Manifest included in archive" 