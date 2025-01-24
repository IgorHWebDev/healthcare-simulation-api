#!/bin/bash

# IQHIS Project Backup Script
# This script creates comprehensive backups of all critical project components

# Configuration
BACKUP_ROOT="/backup/iqhis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"

# Ensure backup directory exists
mkdir -p "${BACKUP_DIR}"

# 1. Documentation Backup
echo "Backing up documentation..."
mkdir -p "${BACKUP_DIR}/docs"
cp -r ./docs/* "${BACKUP_DIR}/docs/"

# 2. Source Code Backup
echo "Backing up source code..."
mkdir -p "${BACKUP_DIR}/src"
cp -r ./agents "${BACKUP_DIR}/src/"
cp -r ./services "${BACKUP_DIR}/src/"

# 3. Configuration Backup
echo "Backing up configurations..."
mkdir -p "${BACKUP_DIR}/config"
# Docker configurations
cp docker-compose*.yml "${BACKUP_DIR}/config/"
# Environment files
cp .env* "${BACKUP_DIR}/config/"
# CI/CD configurations
cp -r .github "${BACKUP_DIR}/config/"

# 4. Database Backup
echo "Backing up database schemas..."
mkdir -p "${BACKUP_DIR}/database"
# Add database backup commands here based on your specific database
# Example for PostgreSQL:
# pg_dump -U postgres -F t iqhis > "${BACKUP_DIR}/database/iqhis.tar"

# 5. Security Configurations
echo "Backing up security configurations..."
mkdir -p "${BACKUP_DIR}/security"
# Backup public keys and security configurations (not private keys!)
cp -r ./security/public/* "${BACKUP_DIR}/security/"
cp -r ./security/config/* "${BACKUP_DIR}/security/"

# 6. Test Data and Configurations
echo "Backing up test configurations..."
mkdir -p "${BACKUP_DIR}/tests"
cp -r ./tests "${BACKUP_DIR}/tests/"

# 7. Dependencies
echo "Backing up dependency configurations..."
cp requirements*.txt "${BACKUP_DIR}/"
cp package*.json "${BACKUP_DIR}/"
cp poetry.lock pyproject.toml "${BACKUP_DIR}/" 2>/dev/null

# 8. Create Archive
echo "Creating compressed archive..."
cd "${BACKUP_ROOT}"
tar -czf "iqhis_backup_${TIMESTAMP}.tar.gz" "${TIMESTAMP}"

# 9. Cleanup
echo "Cleaning up temporary files..."
rm -rf "${BACKUP_DIR}"

echo "Backup completed: ${BACKUP_ROOT}/iqhis_backup_${TIMESTAMP}.tar.gz"

# Optional: Retain only last N backups
MAX_BACKUPS=5
cd "${BACKUP_ROOT}"
ls -t iqhis_backup_*.tar.gz | tail -n +$((MAX_BACKUPS + 1)) | xargs rm -f 2>/dev/null

exit 0 